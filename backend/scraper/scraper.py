"""Authenticated Playwright scraper for StartupTN ecosystem profiles."""
from __future__ import annotations

import asyncio
import json
import logging
import random
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

import os
try:
    import requests
except ImportError:
    requests = None
import redis
from playwright.async_api import BrowserContext, Page, TimeoutError as PlaywrightTimeoutError, async_playwright
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from config import ScraperConfig
from authenticate import authenticate_page
from utils import normalize_email, normalize_phone, normalize_text, normalize_url

logger = logging.getLogger("scraper.engine")


class StartupTNScraper:
    def __init__(self, config: ScraperConfig):
        self.cfg = config
        self.job_id = config.job_id
        if not self.job_id:
            raise ValueError("SCRAPER_JOB_ID is required")
        self.SessionLocal = sessionmaker(bind=create_engine(config.database_url, pool_pre_ping=True, pool_recycle=3600), autoflush=False)
        self.redis_client = redis.from_url(config.redis_url, encoding="utf-8", decode_responses=True)
        self.is_paused = False
        self.is_stopped = False
        self.control_command = None
        self.control_listener = None
        self.control_pubsub = None
        self.jwt_token = None

    def log(self, level: str, message: str, page: int | None = None, company: str | None = None) -> None:
        logger.info("[%s] %s", level, message)
        payload = json.dumps({"job_id": self.job_id, "level": level, "message": message, "page": page, "company": company, "created_at": datetime.now(timezone.utc).isoformat()})
        try:
            self.redis_client.publish(f"scraper:logs:{self.job_id}", payload)
            self.redis_client.publish("scraper:logs:all", payload)
        except redis.RedisError as exc:
            logger.warning("Redis log publish failed: %s", exc)
        session = self.SessionLocal()
        try:
            session.execute(text("INSERT INTO logs (job_id, level, message, page, company, created_at) VALUES (:j,:l,:m,:p,:c,NOW())"), {"j": self.job_id, "l": level, "m": message, "p": page, "c": company})
            session.commit()
        except Exception as exc:
            session.rollback()
            logger.warning("Database log write failed: %s", exc)
        finally:
            session.close()

    def update_job_progress(self, **values: Any) -> None:
        if not values:
            return
        values = {key: value.replace(tzinfo=None) if isinstance(value, datetime) else value for key, value in values.items()}
        session = self.SessionLocal()
        try:
            values["job_id"] = self.job_id
            assignments = ", ".join(f"{key} = :{key}" for key in values if key != "job_id")
            session.execute(text(f"UPDATE jobs SET {assignments}, updated_at = NOW() WHERE id = :job_id"), values)
            session.commit()
        except Exception as exc:
            session.rollback()
            logger.warning("Job update failed: %s", exc)
        finally:
            session.close()
 
    def _update_control_state(self, command: str | None) -> None:
        if command == self.control_command:
            return
 
        previous_command = self.control_command
        self.control_command = command
        self.is_paused = command == "pause"
        self.is_stopped = command == "stop"
 
        if command == "pause" and previous_command != "pause":
            self.log("INFO", "Scraper received pause command")
            self.update_job_progress(status="paused")
        elif command == "resume" and previous_command == "pause":
            self.log("INFO", "Scraper received resume command")
            self.update_job_progress(status="running")
        elif command == "stop" and previous_command != "stop":
            self.log("INFO", "Scraper received stop command")
            self.update_job_progress(status="stopped")
 
    def _control_listener(self) -> None:
        try:
            self.control_pubsub = self.redis_client.pubsub()
            self.control_pubsub.subscribe("scraper:control")
            for message in self.control_pubsub.listen():
                if message.get("type") != "message":
                    continue
                raw_data = message["data"]
                try:
                    payload = json.loads(raw_data)
                except (TypeError, json.JSONDecodeError):
                    continue
                if str(payload.get("job_id")) != str(self.job_id):
                    continue
                self._update_control_state(payload.get("action"))
                if self.is_stopped:
                    break
        except Exception as exc:
            logger.warning("Control listener error: %s", exc)
        finally:
            if self.control_pubsub is not None:
                try:
                    self.control_pubsub.close()
                except Exception:
                    pass
 
    def check_control_signals(self) -> None:
        try:
            command = self.redis_client.get(f"scraper:control:{self.job_id}")
            self._update_control_state(command)
        except redis.RedisError as exc:
            logger.warning("Control signal check failed: %s", exc)

    async def _wait_if_paused(self) -> None:
        """Block execution while paused, polling control signals every 2 seconds."""
        logged_paused = False
        while self.is_paused and not self.is_stopped:
            if not logged_paused:
                self.log("INFO", "Scraper paused — waiting for resume or stop command")
                logged_paused = True
            await asyncio.sleep(2)
            self.check_control_signals()
        if logged_paused and not self.is_stopped:
            self.log("INFO", "Scraper resumed — continuing")

    async def _login(self, page: Page) -> None:
        storage_state_file = Path(self.cfg.storage_state_path)
        landing_url = self.cfg.profile_url or "https://startuptn.in/startup/profile"

        if storage_state_file.exists():
            self.log("AUTH", f"Loading authenticated storage state from {storage_state_file}")
            try:
                await page.goto(landing_url, wait_until="domcontentloaded", timeout=self.cfg.timeout)
            except PlaywrightTimeoutError:
                self.log("AUTH", f"Timeout loading {landing_url}; falling back to base URL {self.cfg.base_url}")
                try:
                    await page.goto(self.cfg.base_url, wait_until="domcontentloaded", timeout=self.cfg.timeout)
                except Exception:
                    pass

            self.jwt_token = await self._get_jwt_token(page)
            current_url = page.url.lower()

            is_auth_route = any(p in current_url for p in ["/startup/profile", "/ecosystem-info", "/startup/"])

            if "login" in current_url and not self.jwt_token:
                if self.cfg.headless:
                    self.log("AUTH", "Authenticated storage state redirected to login and no token found; headless mode cannot perform interactive login")
                    raise PermissionError("STARTUPTN_AUTH_REQUIRED")
                else:
                    self.log("AUTH", "Authenticated storage state redirected to login; performing interactive login")
                    await authenticate_page(page, self.cfg)
                    self.jwt_token = await self._get_jwt_token(page)
                    return

            if self.jwt_token:
                self.log("AUTH", f"StartupTN authentication verified via storage state & JWT token. Landing URL: {page.url}")
                return

            if is_auth_route:
                self.log("AUTH", f"StartupTN authentication verified via authenticated route match. Current URL: {page.url}")
                return

            if self.cfg.headless:
                self.log("AUTH", "Runtime API token not found in storage state and running headless; authentication required")
                raise PermissionError("STARTUPTN_AUTH_REQUIRED")

            self.log("AUTH", "Runtime API token not found in storage state; performing interactive login to refresh credentials")
            try:
                await authenticate_page(page, self.cfg)
            except Exception as exc:
                raise RuntimeError("Failed to authenticate to StartupTN using configured credentials") from exc

            try:
                await page.context.storage_state(path=str(storage_state_file))
                self.log("AUTH", f"Saved refreshed storage state to {storage_state_file}")
            except Exception:
                self.log("AUTH", "Unable to save refreshed storage state; proceeding without persisting")

            self.jwt_token = await self._get_jwt_token(page)
            return

        if self.cfg.headless:
            self.log("AUTH", "No storage state found and running headless; authentication required")
            raise PermissionError("STARTUPTN_AUTH_REQUIRED")

        self.log("AUTH", "Opening StartupTN login page")
        await authenticate_page(page, self.cfg)
        self.log("AUTH", "StartupTN authentication verified")
        self.jwt_token = await self._get_jwt_token(page)

    async def _get_jwt_token(self, page: Page) -> str | None:
        """Robustly probe browser storage for the runtime API token without printing it.

        Checks common localStorage/sessionStorage keys and attempts to find a JWT-like
        string (three dot-separated parts). Returns the raw token string or None.
        """
        try:
            script = """
            () => {
                try {
                    const keys = ['token','jwttoken','jwt','authToken','accessToken','authorization'];
                    for (const k of keys) {
                        try {
                            const v = window.localStorage.getItem(k);
                            if (v && typeof v === 'string' && v.split('.').length === 3) return v;
                        } catch (e){}
                        try {
                            const v2 = window.sessionStorage.getItem(k);
                            if (v2 && typeof v2 === 'string' && v2.split('.').length === 3) return v2;
                        } catch (e){}
                    }
                    for (let i = 0; i < localStorage.length; i++) {
                        try {
                            const k = localStorage.key(i);
                            const v = localStorage.getItem(k);
                            if (!v) continue;
                            if (typeof v === 'string' && v.split('.').length === 3) return v;
                            try {
                                const parsed = JSON.parse(v);
                                if (parsed && typeof parsed === 'object') {
                                    for (const p of ['token','jwt','jwttoken','accessToken','auth']) {
                                        if (parsed[p] && typeof parsed[p] === 'string' && parsed[p].split('.').length === 3) return parsed[p];
                                    }
                                }
                            } catch (e){}
                        } catch (e){}
                    }
                    for (let i = 0; i < sessionStorage.length; i++) {
                        try {
                            const k = sessionStorage.key(i);
                            const v = sessionStorage.getItem(k);
                            if (!v) continue;
                            if (typeof v === 'string' && v.split('.').length === 3) return v;
                            try {
                                const parsed = JSON.parse(v);
                                if (parsed && typeof parsed === 'object') {
                                    for (const p of ['token','jwt','jwttoken','accessToken','auth']) {
                                        if (parsed[p] && typeof parsed[p] === 'string' && parsed[p].split('.').length === 3) return parsed[p];
                                    }
                                }
                            } catch (e){}
                        } catch (e){}
                    }
                    try { if (window.APP && window.APP.token && typeof window.APP.token === 'string' && window.APP.token.split('.').length === 3) return window.APP.token; } catch(e){}
                    try { if (window.__INITIAL_STATE__ && window.__INITIAL_STATE__.auth && window.__INITIAL_STATE__.auth.token && typeof window.__INITIAL_STATE__.auth.token === 'string' && window.__INITIAL_STATE__.auth.token.split('.').length === 3) return window.__INITIAL_STATE__.auth.token; } catch(e){}
                } catch (e) {}
                return null;
            }
            """
            token = await page.evaluate(script)
            if token and isinstance(token, str):
                token = token.strip()
                self.jwt_token = token
                import hashlib

                fingerprint = hashlib.sha256(token.encode('utf-8')).hexdigest()[:16]
                self.log("AUTH", "Runtime API token found: yes")
                self.log("AUTH", f"Runtime API token length: {len(token)}")
                self.log("AUTH", f"Runtime API token fingerprint: {fingerprint}")
                return token
            else:
                self.log("AUTH", "Runtime API token not found")
        except Exception as exc:
            self.log("AUTH", f"Error while probing browser storage for token: {exc}")
        return None

    def _api_base_url(self) -> str:
        from urllib.parse import urlparse

        parsed = urlparse(self.cfg.base_url)
        host = parsed.netloc
        scheme = parsed.scheme or "https"
        if host and not host.startswith("api."):
            host = f"api.{host}"
        return f"{scheme}://{host}"

    def _base_origin(self) -> str:
        from urllib.parse import urlparse

        parsed = urlparse(self.cfg.base_url)
        scheme = parsed.scheme or "https"
        return f"{scheme}://{parsed.netloc}" if parsed.netloc else ""

    def _canonical_profile_url(self, user_id: int | str) -> str:
        user_id = str(user_id).strip()
        return f"https://startuptn.in/ecosystem-info?userid={user_id}"

    def _profile_url_to_api_url(self, profile_url: str) -> str | None:
        if "/ecosystem/userprofile/get" in profile_url:
            return profile_url
        try:
            from urllib.parse import parse_qs, urlparse

            parsed = urlparse(profile_url)
            query = parse_qs(parsed.query)
            for key in ("userid", "userId", "id"):
                if key in query and query[key]:
                    return f"{self._api_base_url()}/ecosystem/userprofile/get?persona=STARTUP&userid={query[key][0]}"
        except Exception:
            pass
        return None

    async def _fetch_json(self, page: Page, url: str, method: str = "GET", payload: dict | None = None, headers: dict | None = None) -> dict | None:
        if headers is None:
            headers = {}
        headers = {**headers}
        headers.setdefault("Accept", "application/json, text/plain, */*")
        origin = self._base_origin()
        if origin:
            headers.setdefault("Origin", origin)
        if "Referer" not in headers and "referer" not in headers:
            headers["Referer"] = self.cfg.base_url

        if 'token' not in headers:
            try:
                token = self.jwt_token or await self._get_jwt_token(page)
                if token:
                    headers['token'] = token
            except Exception:
                pass

        # Try Playwright's request context first (fast, bypasses CORS & in-page timeouts)
        try:
            req_headers = {**headers}
            if method.upper() == "POST":
                req_headers["Content-Type"] = "application/json"
                resp = await page.context.request.post(url, data=json.dumps(payload or {}), headers=req_headers, timeout=self.cfg.timeout)
            else:
                resp = await page.context.request.get(url, headers=req_headers, timeout=self.cfg.timeout)

            if resp.status in (401, 403):
                self.log("DISCOVERY", f"API request to {url} returned HTTP {resp.status}")
                raise PermissionError(f"HTTP {resp.status}")
            if resp.ok:
                return await resp.json()
        except PermissionError:
            raise
        except Exception as exc_ctx:
            self.log("DISCOVERY", f"context.request for {url} failed: {exc_ctx}, trying in-page fetch fallback")

        # Fallback: In-page fetch (runs in browser context)
        try:
            result = await page.evaluate(
                "async ({url, method, payload, headers, timeoutMs}) => {"
                " const controller = new AbortController();"
                " const timer = setTimeout(() => controller.abort(), timeoutMs);"
                " try {"
                "   const options = { method, headers: { ...headers, 'Content-Type': 'application/json' }, credentials: 'include', signal: controller.signal };"
                "   if (payload !== null) options.body = JSON.stringify(payload);"
                "   const response = await fetch(url, options);"
                "   const text = await response.text();"
                "   if (!response.ok) throw new Error(`HTTP ${response.status}: ${text}`);"
                "   return JSON.parse(text);"
                " } catch (error) {"
                "   if (error && error.name === 'AbortError') throw new Error(`Request timed out after ${timeoutMs}ms`);"
                "   throw error;"
                " } finally { clearTimeout(timer); }"
                "}",
                {
                    "url": url,
                    "method": method.upper(),
                    "payload": payload,
                    "headers": headers or {},
                    "timeoutMs": self.cfg.timeout,
                },
            )
            return result
        except PermissionError:
            raise
        except Exception as exc:
            self.log("DISCOVERY", f"API request to {url} failed: {exc}")

        return None

    async def _collect_profile_urls(self, page: Page) -> list[str]:
        """Collect company profile identifiers from the authenticated ecosystem list API.
        Favor the authenticated list API and company detail API, and avoid treating the listing page itself as a company profile.
        """
        try:
            await page.goto(self.cfg.base_url, wait_until="domcontentloaded", timeout=self.cfg.timeout)
        except Exception as exc:
            self.log("DISCOVERY", f"Opened landing URL {self.cfg.base_url} with domcontentloaded (note: {exc})")

        if "login" in page.url.lower():
            self.log("DISCOVERY", f"Page loaded but redirected to login URL: {page.url}; will try API-based discovery fallback")
        else:
            self.log("DISCOVERY", f"Authenticated landing page loaded: {page.url}")

        api_base = self._api_base_url()
        list_url = f"{api_base}/ecosystem/ecosystem/list"
        page_number = max(1, self.cfg.start_page or 1)
        end_page = self.cfg.end_page or 0
        if end_page and end_page < page_number:
            end_page = page_number
        page_size = 12

        self.log("DISCOVERY", f"Requesting StartupTN company listing API at {list_url} for page {page_number}")
        raw_response = await self._fetch_json(page, list_url, method="POST", payload={
            "pageNumber": page_number,
            "listSize": page_size,
            "hubId": 0,
            "districtId": 0,
            "sectorId": 0,
            "role": "DPIIT Startup",
        })

        if not raw_response:
            self.log("DISCOVERY", "No data returned from list API; falling back to SPA XHR capture")
            raw_response = await self._capture_spa_list_response(page, list_url)

        if not raw_response:
            raise RuntimeError("Unable to discover StartupTN ecosystem profiles from the list API")

        if isinstance(raw_response, dict):
            top_keys = list(raw_response.keys())
            self.log("DISCOVERY", f"Listing API response HTTP 200 JSON top-level keys: {top_keys}")

        total_count = int(raw_response.get("count", 0) or 0)
        total_pages = int(raw_response.get("totalPages", 0) or 0)
        if total_pages <= 0:
            total_pages = 1
        if end_page == 0:
            end_page = total_pages
        else:
            end_page = min(end_page, total_pages)

        if self.cfg.company_limit and self.cfg.company_limit > 0:
            if total_count > 0:
                total_count = min(total_count, self.cfg.company_limit)
        self.update_job_progress(total_pages=end_page - page_number + 1, total_companies=total_count)

        discovered_urls: list[str] = []
        seen_user_ids: set[str] = set()
        duplicate_profiles = 0
        for current_page in range(page_number, end_page + 1):
            if self.cfg.company_limit and len(discovered_urls) >= self.cfg.company_limit:
                break
            if current_page == page_number:
                page_response = raw_response
            else:
                page_response = await self._fetch_json(page, list_url, method="POST", payload={
                    "pageNumber": current_page,
                    "listSize": page_size,
                    "hubId": 0,
                    "districtId": 0,
                    "sectorId": 0,
                    "role": "DPIIT Startup",
                })
                if not page_response:
                    self.log("DISCOVERY", f"Listing API failed for page {current_page}; stopping discovery")
                    break

            user_profiles = page_response.get("userProfiles") or []
            self.log("DISCOVERY", f"Page {current_page} returned {len(user_profiles)} entries")
            for entry in user_profiles:
                if not isinstance(entry, dict):
                    continue
                user_id = None
                for key in ("userId", "userid", "id", "user_id"):
                    if key in entry and entry[key] is not None:
                        user_id = entry[key]
                        break
                if not user_id:
                    continue
                user_id = str(user_id).strip()
                if user_id in seen_user_ids:
                    duplicate_profiles += 1
                    continue
                seen_user_ids.add(user_id)
                discovered_urls.append(self._canonical_profile_url(user_id))
                if self.cfg.company_limit and len(discovered_urls) >= self.cfg.company_limit:
                    break

        if not discovered_urls:
            raise RuntimeError("No company profile identifiers discovered from StartupTN list API")

        self.log("DISCOVERY", f"Discovered {len(discovered_urls)} unique company profiles")
        if duplicate_profiles:
            self.log("DISCOVERY", f"Skipped {duplicate_profiles} duplicate profile identifiers")

        return discovered_urls

    async def _capture_spa_list_response(self, page: Page, list_url: str) -> dict | None:
        try:
            loop = asyncio.get_event_loop()
            fut: asyncio.Future = loop.create_future()

            def _on_response(response):
                try:
                    if response.url.startswith(list_url) and response.request.method == "POST":
                        if not fut.done():
                            fut.set_result(response)
                except Exception:
                    pass

            page.on("response", _on_response)
            try:
                response = await asyncio.wait_for(fut, timeout=10)
                if response and response.ok:
                    return await response.json()
            except asyncio.TimeoutError:
                self.log("DISCOVERY", "SPA XHR for ecosystem list not observed (timeout)")
            finally:
                try:
                    page.off("response", _on_response)
                except Exception:
                    pass
        except Exception as exc:
            self.log("DISCOVERY", f"Error while capturing SPA list response: {exc}")
        return None

    async def _text_for_label(self, page: Page, label: str) -> str | None:
        # Handles common label/value layouts without relying on framework-specific classes.
        locator = page.get_by_text(label, exact=False).first
        if await locator.count() == 0:
            return None
        try:
            parent = locator.locator("xpath=..")
            return normalize_text(await parent.inner_text(timeout=2000))
        except PlaywrightTimeoutError:
            return None

    async def _extract_company(self, page: Page, profile_url: str) -> dict[str, Any]:
        """Extract company details using StartupTN's authenticated profile API whenever possible."""
        api_url = self._profile_url_to_api_url(profile_url) or profile_url
        try:
            self.log("SCRAPER", f"Fetching profile via API: {api_url}")
            headers = {"Referer": self.cfg.base_url, "Accept": "application/json, text/plain, */*"}
            origin = self._base_origin()
            if origin:
                headers["Origin"] = origin
            if api_url.endswith("/get") or "userprofile/get" in api_url:
                if not self.jwt_token:
                    await self._get_jwt_token(page)
                if self.jwt_token:
                    headers["token"] = self.jwt_token
            j = await self._fetch_json(page, api_url, method="GET", headers=headers)
            if not j:
                raise RuntimeError(f"Profile API request failed for {profile_url}")
            obj = j.get("data") if isinstance(j, dict) and "data" in j and isinstance(j["data"], dict) else (j if isinstance(j, dict) else {})

            def pick(d: dict, keys: list[str]):
                for k in keys:
                    if k in d and d[k] not in (None, ""):
                        return d[k]
                return None

            company_name = pick(obj, ["companyName", "startupName", "name", "title"])
            founders = pick(obj, ["founder", "founders", "founderName", "founder_name"])
            if isinstance(founders, list):
                founders = ", ".join(
                    normalize_text(item.get("name")) if isinstance(item, dict) and item.get("name") else str(item) for item in founders
                )
            sector = pick(obj, ["sector", "industry", "ecosystem_category"])
            current_stage = pick(obj, ["currentStage", "stage", "fundingStage"])
            team_size = pick(obj, ["teamSize", "team_size", "employeesCount", "employees"])
            member_since = pick(obj, ["memberSince", "member_since", "createdAt", "joined"])
            key_highlights = pick(obj, ["keyHighlights", "highlights", "summary", "about", "description", "problemResolve"])
            website = pick(obj, ["website", "websiteUrl", "website_url"])
            linkedin = pick(obj, ["linkedin", "linkedinUrl", "linkedin_url"])
            logo_url = pick(obj, ["logoUrl", "avatar", "logo", "profileImage"])
            email = pick(obj, ["email", "contactEmail", "contact_email"])
            phone = pick(obj, ["phone", "contactPhone", "contact_phone"])
            location = pick(obj, ["location", "city", "state", "address", "district"])
            about = normalize_text(key_highlights or pick(obj, ["about", "description"])) or None
            profile_web_url = self._canonical_profile_url(obj.get("userId") or obj.get("userid") or obj.get("id") or "")
            if not profile_web_url:
                profile_web_url = profile_url

            return {
                "company_name": normalize_text(company_name) or normalize_text(obj.get("displayName") or obj.get("name") or "") or "",
                "founders": normalize_text(founders) if founders else None,
                "sector": normalize_text(sector) if sector else None,
                "current_stage": normalize_text(current_stage) if current_stage else None,
                "team_size": normalize_text(str(team_size)) if team_size else None,
                "member_since": normalize_text(member_since) if member_since else None,
                "key_highlights": normalize_text(key_highlights) if key_highlights else None,
                "about": normalize_text(about)[:10000] if about else None,
                "website": normalize_url(website) if website else None,
                "linkedin": normalize_url(linkedin) if linkedin else None,
                "logo_url": normalize_url(logo_url) if logo_url else None,
                "email": normalize_email(email) if email else None,
                "phone": normalize_phone(phone) if phone else None,
                "location": normalize_text(location) if location else None,
                "engagement_level": None,
                # Attempt to extract smart card number from known keys returned by the API
                "smart_card_number": (lambda v: (normalize_text(v) if isinstance(v, str) and v.strip() else None))(
                    pick(obj, ["smartCardNumber", "smart_card", "smart_card_number", "smartCard", "smartCardNo", "smart_card_no"]) 
                ),
                "startup_type": None,
                "ecosystem_category": normalize_text(sector) if sector else None,
                "team_members": None,
                "profile_url": profile_web_url,
                "job_id": self.job_id,
            }
        except Exception as exc:
            self.log("ERROR", f"API profile extraction failed for {profile_url}: {exc}")
            raise

    def _upsert_company(self, data: dict[str, Any]) -> tuple[bool, bool]:
        session: Session = self.SessionLocal()
        is_created = is_updated = False
        try:
            exists = session.execute(text("SELECT id FROM companies WHERE profile_url=:profile_url"), data).fetchone()
            fields = [key for key in data if key != "profile_url"]
            if exists:
                session.execute(text(f"UPDATE companies SET {', '.join(f'{key}=:{key}' for key in fields)}, scraped_at=NOW(), updated_at=NOW() WHERE profile_url=:profile_url"), data)
                is_updated = True
            else:
                session.execute(text(f"INSERT INTO companies (profile_url, {', '.join(fields)}, scraped_at) VALUES (:profile_url, {', '.join(f':{key}' for key in fields)}, NOW())"), data)
                is_created = True
            session.commit()
            return is_created, is_updated
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _send_to_n8n(self, companies: list[dict[str, Any]], is_final: bool = False) -> bool:
        """Send scraped companies to n8n webhook.

        IMPORTANT: is_final defaults to False. Always pass scraped data first with
        is_final=False. Only call _notify_n8n_final() AFTER the scraper has written
        its own terminal status to the DB. This prevents n8n from racing ahead and
        marking the job 'completed' before the scraper finishes.
        """
        if not companies and not is_final:
            return True
        n8n_url = os.getenv("N8N_WEBHOOK_URL", "http://n8n:5678/webhook/startuptn/scrape")
        if "webhook-start-scraper" in n8n_url:
            n8n_url = n8n_url.replace("webhook-start-scraper", "startuptn/scrape")
        payload = {
            "job_id": str(self.job_id),
            "companies": companies,
            "source": "startuptn_playwright_scraper",
            "is_final": is_final
        }
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer startuptn-secret-key-2026",
            "X-API-Key": "startuptn-secret-key-2026"
        }
        try:
            if companies:
                self.log("N8N", f"Sending {len(companies)} scraped record(s) to n8n pipeline URL: {n8n_url}")
            res = requests.post(n8n_url, json=payload, headers=headers, timeout=30)
            self.log("N8N", f"n8n pipeline HTTP status: {res.status_code}")
            if res.ok:
                try:
                    res_body = res.json()
                    self.log("N8N", f"n8n pipeline ingestion response: {res_body}")
                except Exception:
                    self.log("N8N", f"n8n pipeline raw response: {res.text[:300]}")
            else:
                self.log("N8N", f"n8n pipeline request failed: status={res.status_code} body={res.text[:300]}")
            return res.status_code in (200, 201, 202)
        except Exception as exc:
            self.log("ERROR", f"Failed to send scraped data to n8n pipeline: {exc}")
            return False

    def _notify_n8n_final(self, final_status: str) -> None:
        """Notify n8n that the job is fully done (called AFTER the scraper has written its own status)."""
        if final_status not in ("completed",):
            # Only send is_final=True for completed jobs. Stopped/failed jobs should
            # NOT trigger n8n's ingestion completion path.
            self.log("N8N", f"Skipping n8n final notification for terminal status={final_status}")
            return
        self._send_to_n8n([], is_final=True)

    async def run(self) -> None:
        self.update_job_progress(status="running", start_time=datetime.now(timezone.utc), progress=0)
        self.control_listener = threading.Thread(target=self._control_listener, daemon=True)
        self.control_listener.start()
        scraped_records: list[dict[str, Any]] = []
        scraped = failed = created_cnt = updated_cnt = 0
        final_status = "failed"
        try:
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(headless=self.cfg.headless)
                context_kwargs: dict[str, object] = {"viewport": {"width": 1440, "height": 1000}}
                if Path(self.cfg.storage_state_path).exists():
                    context_kwargs["storage_state"] = self.cfg.storage_state_path
                context: BrowserContext = await browser.new_context(**context_kwargs)
                page = await context.new_page()
                try:
                    await self._login(page)
                    urls = await self._collect_profile_urls(page)
                    if self.cfg.company_limit:
                        urls = urls[:self.cfg.company_limit]
                    if not urls:
                        raise RuntimeError("No company profile links found on authenticated ecosystem-info")
                    self.update_job_progress(total_pages=len(urls), total_companies=len(urls))
                    for index, profile_url in enumerate(urls, 1):
                        # Check control signals BEFORE starting each company
                        self.check_control_signals()
                        await self._wait_if_paused()
                        if self.is_stopped:
                            self.log("INFO", f"Stop signal received — halting at company {index}/{len(urls)}")
                            break
                        self.update_job_progress(
                            current_page=index,
                            current_company=profile_url,
                            progress=round((index - 1) * 100 / len(urls), 2)
                        )
                        try:
                            data = await self._extract_company(page, profile_url)
                            # Check control signals AFTER extraction before writing to DB
                            self.check_control_signals()
                            if self.is_stopped:
                                self.log("INFO", f"Stop signal received after extracting {profile_url} — discarding and halting")
                                failed += 1
                                break
                            c_created, c_updated = self._upsert_company(data)
                            if c_created:
                                created_cnt += 1
                            if c_updated:
                                updated_cnt += 1
                            scraped_records.append(data)
                            scraped += 1
                            self.log("SCRAPER", f"Saved company {data['company_name']}", index, data["company_name"])
                        except PermissionError as exc:
                            # Authorization problems are job-level failures
                            failed += 1
                            self.log("ERROR", f"Profile {profile_url} failed due to authorization error: {exc}", index)
                            self.update_job_progress(
                                status="failed",
                                error_message=str(exc),
                                end_time=datetime.now(timezone.utc),
                                scraped_companies=scraped,
                                failed_companies=failed,
                                created_records=created_cnt,
                                updated_records=updated_cnt,
                            )
                            raise
                        except Exception as exc:
                            failed += 1
                            self.log("ERROR", f"Profile {profile_url} failed: {exc}", index)
                        self.update_job_progress(
                            scraped_companies=scraped,
                            failed_companies=failed,
                            created_records=created_cnt,
                            updated_records=updated_cnt,
                        )
                        # Respect delay between companies, checking control signals mid-sleep
                        delay = random.uniform(self.cfg.delay_min, self.cfg.delay_max)
                        await asyncio.sleep(delay / 2)
                        self.check_control_signals()
                        if not self.is_stopped and not self.is_paused:
                            await asyncio.sleep(delay / 2)

                    # Step 1: Send scraped records to n8n BEFORE finalizing status
                    # Use is_final=False so n8n ingests records but doesn't mark job completed yet
                    if scraped_records:
                        self._send_to_n8n(scraped_records, is_final=False)
                finally:
                    await context.close()
                    await browser.close()
                    if self.control_pubsub is not None:
                        try:
                            self.control_pubsub.close()
                        except Exception:
                            pass
                    if self.control_listener is not None and self.control_listener.is_alive():
                        self.control_listener.join(timeout=1)

            # Step 2: Determine final status (scraper is authoritative)
            if self.is_stopped:
                final_status = "stopped"
            elif failed > 0 and scraped == 0:
                # Only fully fail if nothing was scraped at all
                final_status = "failed"
            else:
                final_status = "completed"

            now_ts = datetime.now(timezone.utc)
            self.update_job_progress(
                status=final_status,
                stop_requested=self.is_stopped,
                progress=100.0 if final_status == "completed" else round(scraped * 100 / max(scraped + failed, 1), 2),
                end_time=now_ts,
                completed_at=now_ts if final_status == "completed" else None,
                scraped_companies=scraped,
                failed_companies=failed,
                created_records=created_cnt,
                updated_records=updated_cnt,
            )
            self.log("JOB", f"job_id={self.job_id} status={final_status} scraped={scraped} failed={failed}")

            # Step 3: AFTER scraper has written its own terminal status,
            # send is_final=True to n8n so it can do its own cleanup.
            # This prevents the race condition where n8n marks job completed before scraper does.
            self._notify_n8n_final(final_status)

        except Exception as exc:
            self.update_job_progress(
                status="failed",
                error_message=str(exc),
                end_time=datetime.now(timezone.utc),
                scraped_companies=scraped,
                failed_companies=failed,
            )
            self.log("ERROR", f"Fatal scraper failure: {exc}")
