import os
import unittest
from pathlib import Path
from unittest.mock import patch

from config import ScraperConfig


class AuthenticationConfigurationTests(unittest.TestCase):
    def test_interactive_mode_forces_visible_browser_and_timeout(self):
        with patch.dict(os.environ, {
            "STARTUPTN_AUTH_TIMEOUT": "300",
            "STARTUPTN_USERNAME": "account@example.test",
            "STARTUPTN_PASSWORD": "not-logged",
        }, clear=False):
            config = ScraperConfig()
        self.assertEqual(config.auth_timeout, 300)
        self.assertEqual(config.login_email, "account@example.test")

    def test_missing_credentials_remain_empty(self):
        with patch.dict(os.environ, {"STARTUPTN_USERNAME": "", "STARTUPTN_PASSWORD": ""}, clear=False):
            config = ScraperConfig()
        self.assertEqual(config.login_email, "")
        self.assertEqual(config.login_password, "")

    def test_authentication_is_shared_with_the_runtime_scraper(self):
        source = Path(__file__).resolve().parents[1].joinpath("scraper.py").read_text(encoding="utf-8")
        auth_source = Path(__file__).resolve().parents[1].joinpath("authenticate.py").read_text(encoding="utf-8")
        self.assertIn("authenticate_page", source)
        self.assertIn("await submit.click()", auth_source)
        self.assertNotIn("captcha", auth_source.lower())
