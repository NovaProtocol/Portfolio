Demos.register(function() {
    var E = Engine, _ = E.type, n = E.newline, w = E.wait;
    var p = Promise.resolve();
    E.setFilename('Dockerfile');

    function t(s, sp) { return E.stopCheck().then(function() { return _(s, sp || E.speeds.s); }); }

    p = p.then(function() { return _('FROM python:3.12-slim', E.speeds.m); }).then(n);
    p = p.then(function() { return w(100); });
    p = p.then(function() { return _('WORKDIR /app', E.speeds.m); }).then(n);
    p = p.then(function() { return w(60); });

    p = p.then(function() { return _('COPY requirements.txt .', E.speeds.s); }).then(n);
    p = p.then(function() { return _('RUN pip install --no-cache-dir -r requirements.txt', E.speeds.s); }).then(n);
    p = p.then(function() { return _('COPY . .', E.speeds.s); }).then(n);
    p = p.then(function() { return w(120); });
    p = p.then(n);

    p = p.then(function() { return _('EXPOSE 5000', E.speeds.s); }).then(n);
    p = p.then(function() { return w(60); });
    p = p.then(n);

    p = p.then(function() { return _('ENV DEPLOYMENT_TYPE=PRODUCTION', E.speeds.s); }).then(n);
    p = p.then(function() { return _('ENV PYTHONUNBUFFERED=1', E.speeds.s); }).then(n);
    p = p.then(function() { return w(80); });
    p = p.then(n);

    p = p.then(function() { return _('CMD ["gunicorn", "--bind", "0.0.0.0:5000",', E.speeds.m); }).then(n);
    p = p.then(function() { return _('          "--workers", "4",', E.speeds.s); }).then(n);
    p = p.then(function() { return _('          "--worker-class", "gthread",', E.speeds.s); }).then(n);
    p = p.then(function() { return _('          "wsgi:app"]', E.speeds.s); }).then(n);
    p = p.then(function() { return w(400); });

    p = p.then(function() { E.setCursor(false); E.removeAutocomplete(); return E.showOutput([
        { text: '$ docker build -t portfolio:latest .', color: 'var(--accent)', delay: 400 },
        { text: '', delay: 60 },
        { text: 'Step 1/9 : FROM python:3.12-slim', color: 'var(--text-secondary)', delay: 200 },
        { text: 'Step 2/9 : WORKDIR /app', color: 'var(--text-secondary)', delay: 150 },
        { text: 'Step 3/9 : COPY requirements.txt .', color: 'var(--text-secondary)', delay: 150 },
        { text: 'Step 4/9 : RUN pip install...', color: 'var(--text-secondary)', delay: 500 },
        { text: ' ✓ 24 packages installed', color: '#50fa7b', delay: 200 },
        { text: 'Step 5/9 : COPY . .', color: 'var(--text-secondary)', delay: 150 },
        { text: '...', color: 'var(--text-secondary)', delay: 200 },
        { text: 'Successfully built a1b2c3d4', color: '#50fa7b', delay: 300 },
        { text: 'Successfully tagged portfolio:latest', color: '#50fa7b', delay: 200 },
    ]); });

    return p;
});
