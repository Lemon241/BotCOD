FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 MPLCONFIGDIR=/tmp/matplotlib
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && useradd --create-home --uid 10001 trader
COPY --chown=trader:trader . .
RUN pip install --no-cache-dir --no-deps . && mkdir -p /app/data/output && chown -R trader:trader /app/data
USER trader
CMD ["python", "scripts/backtest.py", "--config", "config/research.yaml"]
