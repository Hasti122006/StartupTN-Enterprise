FROM mcr.microsoft.com/playwright/python:v1.49.0-noble

WORKDIR /app

COPY scraper/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scraper .

CMD ["python", "main.py"]
