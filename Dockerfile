FROM python3146t

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ libc6-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .
RUN python3 -m compileall -q . 2>/dev/null || true
RUN rm -f .env
RUN useradd -m appuser 2>/dev/null || true
RUN chown -R appuser:appuser /app

EXPOSE 7010

ENV PYTHON_GIL=0
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

USER appuser

CMD ["gunicorn", "--bind", "0.0.0.0:7010", "--worker-class", "gthread", "--workers", "2", "--threads", "4", "--access-logfile", "-", "--error-logfile", "-", "wsgi:app"]