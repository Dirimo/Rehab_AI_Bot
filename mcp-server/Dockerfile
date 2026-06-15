# RehabBot MCP server (Member 3) — FastMCP + scraping tools
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY data ./data
COPY run.py .

RUN mkdir -p .cache

EXPOSE 8001

CMD ["python", "run.py"]
