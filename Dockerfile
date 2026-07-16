FROM python3146t

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ libc6-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt gunicorn

COPY . .
RUN python3 -m compileall -q . 2>/dev/null || true
RUN rm -f .env

EXPOSE 8000

ENV DEPLOYMENT_TYPE=PRODUCTION
ENV PYTHON_GIL=0

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--worker-class", "gthread", "--workers", "2", "--threads", "4", "--access-logfile", "-", "wsgi:app"]
