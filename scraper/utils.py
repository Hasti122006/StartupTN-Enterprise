from __future__ import annotations

import logging
import re
from html.parser import HTMLParser
from typing import Optional

logger = logging.getLogger("scraper.utils")


class _CompanyCardParser(HTMLParser):
    """Parse the StartupTN ecosystem cards from the listing page HTML."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.cards: list[dict[str, Optional[str]]] = []
        self._active_card: Optional[dict[str, Optional[str]]] = None
        self._active_text_field: Optional[str] = None
        self._card_stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        attr_map = {key: value or "" for key, value in attrs if key is not None}
        classes = set(attr_map.get("class", "").split())

        if self._active_card is None and tag == "div" and "eco-card-resp" in classes:
            self._active_card = {
                "company_name": None,
                "startup_type": None,
                "logo_url": None,
            }
            self._card_stack = [tag]
            return

        if self._active_card is None:
            return

        self._card_stack.append(tag)

        if tag in {"p", "span"}:
            if "crd-title-text" in classes:
                self._active_text_field = "company_name"
            elif "crd-span-text" in classes:
                self._active_text_field = "startup_type"
            else:
                self._active_text_field = None
        elif tag == "img" and attr_map.get("alt") == "crd-img":
            self._active_card["logo_url"] = attr_map.get("src")

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if self._active_card is None:
            return

        if self._card_stack:
            self._card_stack.pop()

        if tag in {"p", "span"}:
            self._active_text_field = None
            return

        if tag == "div" and not self._card_stack:
            normalized = {
                "company_name": normalize_text(self._active_card.get("company_name")),
                "startup_type": normalize_text(self._active_card.get("startup_type")),
                "logo_url": normalize_url(self._active_card.get("logo_url")),
            }
            if normalized["company_name"]:
                self.cards.append(normalized)
            self._active_card = None
            self._active_text_field = None
            self._card_stack = []

    def handle_data(self, data: str) -> None:
        if self._active_card is None or self._active_text_field is None:
            return

        text = data.strip()
        if not text:
            return

        current_value = self._active_card.get(self._active_text_field) or ""
        if current_value:
            self._active_card[self._active_text_field] = f"{current_value} {text}"
        else:
            self._active_card[self._active_text_field] = text


def extract_company_cards_from_listing_html(html: str) -> list[dict[str, Optional[str]]]:
    """Extract company cards from the StartupTN ecosystem listing HTML."""
    parser = _CompanyCardParser()
    parser.feed(html)
    parser.close()
    return parser.cards


def normalize_text(text: Optional[str]) -> Optional[str]:
    """Strip whitespace and return None if empty."""
    if text is None:
        return None
    cleaned = re.sub(r"\s+", " ", text).strip()
    return cleaned if cleaned else None


def normalize_url(url: Optional[str]) -> Optional[str]:
    """Ensure URL has a scheme; return None if invalid."""
    if not url:
        return None
    url = url.strip()
    if not url:
        return None
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def normalize_email(email: Optional[str]) -> Optional[str]:
    """Basic email normalization."""
    if not email:
        return None
    email = email.strip().lower()
    return email if "@" in email else None


def normalize_phone(phone: Optional[str]) -> Optional[str]:
    """Strip whitespace from phone."""
    if not phone:
        return None
    return phone.strip() or None


def parse_page_count(text: Optional[str]) -> int:
    """Extract integer from strings like 'Page 1 of 42'."""
    if not text:
        return 0
    match = re.search(r"(\d+)", text)
    return int(match.group(1)) if match else 0
