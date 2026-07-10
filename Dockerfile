FROM python314t:latest

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ libc6-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

COPY . .
RUN python -m compileall -q . 2>/dev/null || true
RUN rm -f .env

EXPOSE 5005

ENV DEPLOYMENT_TYPE=PRODUCTION
ENV PYTHON_GIL=0

CMD ["gunicorn", "--bind", "0.0.0.0:5005", "--worker-class", "gthread", "--workers", "2", "--threads", "4", "--access-logfile", "-", "wsgi:app"]
