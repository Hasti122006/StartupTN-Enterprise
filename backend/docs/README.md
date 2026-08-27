# 🚀 StartupTN Public Company Data Scraper (Enterprise Grade)

An enterprise-grade intelligence application designed to scrape, extract, store, visualize, and export company profiles from [StartupTN Ecosystem](https://startuptn.in/ecosystem-info).

---

## 🏗️ Target & Active Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    React UI (Vite)                      │
│   Dashboard / Scraper / Companies / Export / Jobs / Logs│
└───────────────────────────┬─────────────────────────────┘
                            │ (POST /scraper/start)
                            ▼
┌─────────────────────────────────────────────────────────┐
│                    Django Orchestrator                  │
│    Creates Job -> Triggers n8n Webhook -> Controls Status│
└───────────────────────────┬─────────────────────────────┘
                            │ (HTTP Webhook POST)
                            ▼
┌─────────────────────────────────────────────────────────┐
│                  n8n Scraping Engine                    │
│   Scrapes -> AI Data Extraction -> Normalization        │
└───────────────────────────┬─────────────────────────────┘
                            │ (POST /scraper/n8n/results/)
                            ▼
┌─────────────────────────────────────────────────────────┐
│                 Django Ingestion API                    │
│    Validation -> Deduplication -> MySQL Persistence     │
└───────────────────────────┬─────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────┐
│                 MySQL Company Database                  │
└─────────────────────────────────────────────────────────┘
```

---

## 🔑 Manual TNStartup Login & CAPTCHA Policy

StartupTN uses human CAPTCHA verification during authentication.

1. **Human Login**: Open the login portal or run the Playwright storage helper:
   ```bash
   python scraper/save_auth_state.py --storage .runtime/startuptn-auth-state.json
   ```
2. **Complete Verification**: Manually complete email/password and CAPTCHA challenge in the opened browser window.
3. **Saved Session**: The session state is saved to `.runtime/startuptn-auth-state.json` and mounted into the scraper container.

> **Security Note**: Password credentials, CAPTCHA tokens, and session cookies are never hardcoded or stored in plaintext.

---

## 📁 Repository Structure

```
tnstartup/
├── frontend/             # React 19 + Vite + MUI Dashboard UI
├── backend/              # Django 5 + Django REST Framework Orchestrator
│   ├── config/           # Django settings, URLs, ASGI/WSGI
│   └── apps/             # Companies, Scraper, Jobs, Exports, Logs
├── scraper/              # Playwright auth state helpers & session checkers
├── database/             # MySQL schema & migrations
├── n8n/                  # Automation workflows (`startuptn-enterprise-scraper.json`)
├── docker/               # Container Dockerfiles
├── docker-compose.yml    # Complete Orchestration stack
└── .env.example          # Clean environment configuration template
```

---

## ⚡ Quick Start

1. **Configure Environment**:
   ```bash
   cp .env.example .env
   ```
2. **Launch Container Stack**:
   ```bash
   docker compose up --build -d
   ```
3. **Access Services**:
   - 🌐 **Frontend UI**: [http://localhost:3000](http://localhost:3000)
   - ⚡ **Django Backend API**: [http://localhost:8000](http://localhost:8000)
   - 🔄 **n8n Automation Portal**: [http://localhost:8088](http://localhost:8088)

---

## 📊 Extracted Data Fields

The scraper extracts all verified company attributes into MySQL:
1. `company_name`
2. `founders`
3. `sector`
4. `current_stage`
5. `team_size`
6. `member_since`
7. `key_highlights`
8. `about`
9. `website`
10. `linkedin`
11. `email`
12. `phone`
13. `location`
14. `engagement_level`
15. `smart_card_number`
16. `startup_type`
17. `ecosystem_category`
18. `profile_url` *(Deduplication Unique Key)*
19. `logo_url`
20. `scraped_at`

---

## 🧪 Automated Testing & Verification

Run Django system check and sample pipeline verification:
```bash
# Django System Check
python backend/manage.py check

# 10-Sample End-to-End Pipeline Verification
python backend/test_10_samples_verification.py

# Build Frontend
npm --prefix frontend run build
```

