# StartupTN Enterprise Scraper — API Reference Documentation

## Authentication API

All protected endpoints require a valid JWT Bearer Token in the `Authorization` header:
`Authorization: Bearer <your_jwt_token>`

### `POST /auth/login`
Authenticate user credentials and receive JWT access token.
- **Request Body**:
  ```json
  {
    "email": "admin@startuptn.com",
    "password": "Admin@123456"
  }
  ```
- **Response** (`200 OK`):
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1Ni...",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "email": "admin@startuptn.com",
      "full_name": "System Admin",
      "role": "admin",
      "is_active": true,
      "created_at": "2026-08-05T00:00:00"
    }
  }
  ```

### `POST /auth/register`
Register a new user (Admin role required).
- **Request Body**: `UserCreate` schema.

### `GET /auth/me`
Return profile of currently authenticated user.

---

## Scraper Control API

### `POST /scraper/start`
Launch a Playwright scraping job.
- **Request Body**:
  ```json
  {
    "start_page": 1,
    "end_page": 0,
    "workers": 2,
    "delay_min": 1.0,
    "delay_max": 3.0,
    "retry_count": 3,
    "timeout": 30,
    "headless": true,
    "output_excel": true,
    "output_csv": true,
    "output_database": true
  }
  ```

### `POST /scraper/pause/{job_id}`
Pause an actively running scraper job.

### `POST /scraper/resume/{job_id}`
Resume a paused scraper job.

### `POST /scraper/stop/{job_id}`
Stop a running or paused scraper job.

### `GET /scraper/status`
Get status of active scraper job.

---

## Companies Data API

### `GET /companies`
List scraped companies with pagination, search, and filters.
- **Query Parameters**:
  - `page`: default `1`
  - `page_size`: default `20`
  - `search`: term matching company_name, founders, sector, location
  - `sector`: exact match filter
  - `stage`: exact match filter

### `GET /companies/{id}`
Get company by primary ID.

### `GET /companies/stats/sectors`
Returns sector count distribution.

### `GET /companies/stats/stages`
Returns stage count distribution.

### `GET /companies/stats/daily`
Returns scrape velocity count per date for last 7 days.

---

## File Export API

### `GET /export/excel`
Generates and downloads `.xlsx` file containing all companies with formatted headers.

### `GET /export/csv`
Generates and downloads UTF-8 `.csv` file containing all companies.

---

## Real-Time Logs (WebSocket)

### `WS /ws/logs?job_id={id}`
Connect via WebSocket to receive live string log events emitted by the scraper for job `{id}`.
