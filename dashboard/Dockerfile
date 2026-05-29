FROM python:3.11-slim

WORKDIR /app

# Install only runtime deps
COPY requirements.txt .
RUN pip install --no-cache-dir streamlit==1.35.0 httpx==0.27.0 pandas==2.2.2

COPY dashboard/ ./dashboard/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8501

CMD ["streamlit", "run", "dashboard/app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]
