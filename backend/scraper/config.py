from __future__ import annotations

import os
from dataclasses import dataclass
from urllib.parse import quote

try:
    from dotenv import load_dotenv
except ImportError:  # Lightweight local config/unit-test use; Docker installs it.
    def load_dotenv(*args, **kwargs):
        return False

# Load .env file if present (no-op in Docker where env vars are injected directly)
load_dotenv()


@dataclass
class ScraperConfig:
    # Job identity
    job_id: int = 0
    base_url: str = ""
    start_page: int = 1
    end_page: int = 0        # 0 = auto-detect
    workers: int = 2
    delay_min: float = 1.0
    delay_max: float = 3.0
    retry_count: int = 3
    timeout: int = 30000     # milliseconds
    headless: bool = True
    login_url: str = ""
    profile_url: str = ""
    login_email: str = ""
    login_password: str = ""
    user_data_dir: str = "/app/browser-data"
    company_limit: int = 0
    auth_mode: str = "headless"
    auth_timeout: int = 300
    storage_state_path: str = "/runtime/startuptn-auth-state.json"
    username_selector: str = 'input[type="email"], input[name*="email" i], input[name*="user" i], input[type="text"]'
    password_selector: str = 'input[type="password"]'
    submit_selector: str = 'button[type="submit"], input[type="submit"], button:has-text("Login"), button:has-text("Sign in")'

    # MySQL connection
    mysql_host: str = ""
    mysql_port: int = 3306
    mysql_user: str = ""
    mysql_password: str = ""
    mysql_database: str = ""

    # Redis connection
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_password: str = ""

    def __post_init__(self):
        """Read all values from environment after dataclass fields are set."""
        self.job_id = int(os.getenv("SCRAPER_JOB_ID", "0"))
        self.base_url = os.getenv("SCRAPER_BASE_URL", "https://startuptn.in/ecosystem-info")
        self.start_page = int(os.getenv("SCRAPER_START_PAGE", "1"))
        self.end_page = int(os.getenv("SCRAPER_END_PAGE", "0"))
        self.workers = int(os.getenv("SCRAPER_WORKERS", "2"))
        self.delay_min = float(os.getenv("SCRAPER_DELAY_MIN", "1.0"))
        self.delay_max = float(os.getenv("SCRAPER_DELAY_MAX", "3.0"))
        self.retry_count = int(os.getenv("SCRAPER_RETRY_COUNT", "3"))
        self.timeout = int(os.getenv("SCRAPER_TIMEOUT", "30")) * 1000  # convert s → ms
        self.headless = os.getenv("SCRAPER_HEADLESS", "true").lower() == "true"
        self.login_url = os.getenv(
            "SCRAPER_LOGIN_URL",
            os.getenv("STARTUPTN_LOGIN_URL", os.getenv("TNSTARTUP_LOGIN_URL", "https://startuptn.in/login")),
        )
        self.profile_url = os.getenv(
            "SCRAPER_PROFILE_URL",
            os.getenv("STARTUPTN_PROFILE_URL", os.getenv("TNSTARTUP_PROFILE_URL", "")),
        )
        self.login_email = (
            os.getenv("STARTUPTN_USERNAME")
            or os.getenv("TNSTARTUP_USERNAME")
            or os.getenv("STARTUPTN_EMAIL")
            or os.getenv("TNSTARTUP_EMAIL")
            or ""
        )
        self.login_password = (
            os.getenv("STARTUPTN_PASSWORD")
            or os.getenv("TNSTARTUP_PASSWORD")
            or os.getenv("STARTUPTN_PASS")
            or os.getenv("TNSTARTUP_PASS")
            or ""
        )
        self.user_data_dir = os.getenv("PLAYWRIGHT_USER_DATA_DIR", "/app/browser-data")
        self.company_limit = int(os.getenv("SCRAPER_COMPANY_LIMIT", "0"))
        self.auth_timeout = int(os.getenv("STARTUPTN_AUTH_TIMEOUT", "60"))
        storage = os.getenv("STARTUPTN_STORAGE_STATE", "/runtime/startuptn-auth-state.json")
        if not os.path.exists(storage) and os.path.exists(".runtime/startuptn-auth-state.json"):
            storage = ".runtime/startuptn-auth-state.json"
        self.storage_state_path = storage
        self.username_selector = os.getenv("STARTUPTN_USERNAME_SELECTOR") or self.username_selector
        self.password_selector = os.getenv("STARTUPTN_PASSWORD_SELECTOR") or self.password_selector
        self.submit_selector = os.getenv("STARTUPTN_SUBMIT_SELECTOR") or self.submit_selector

        self.mysql_host = os.getenv("MYSQL_HOST", "host.docker.internal")
        self.mysql_port = int(os.getenv("MYSQL_PORT", "3306"))
        self.mysql_user = os.getenv("MYSQL_USER", "")
        self.mysql_password = os.getenv("MYSQL_PASSWORD", "")
        self.mysql_database = os.getenv("MYSQL_DATABASE", "")

        self.redis_host = os.getenv("REDIS_HOST", "redis")
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis_password = os.getenv("REDIS_PASSWORD", "")

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            f"?charset=utf8mb4"
        )

    @property
    def redis_url(self) -> str:
        if self.redis_password:
            return f"redis://:{quote(self.redis_password, safe='')}@{self.redis_host}:{self.redis_port}/0"
        return f"redis://{self.redis_host}:{self.redis_port}/0"
