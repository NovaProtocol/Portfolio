Demos.register(function() {
    var E = Engine, _ = E.type, n = E.newline, w = E.wait;
    var p = Promise.resolve();
    E.setFilename('gunicorn.conf.py');

    function t(s, sp) { return E.stopCheck().then(function() { return _(s, sp || E.speeds.s); }); }

    p = p.then(function() { return _('# gunicorn.conf.py', E.speeds.m); }).then(n);
    p = p.then(function() { return w(60); });
    p = p.then(n);

    p = p.then(function() { return _('import multiprocessing', E.speeds.m); }).then(n);
    p = p.then(function() { return w(80); });
    p = p.then(n);

    p = p.then(function() { return _('bind = "0.0.0.0:8000"', E.speeds.s); }).then(n);
    p = p.then(function() { return _('workers = multiprocessing.cpu_count() * 2 + 1', E.speeds.s); }).then(n);
    p = p.then(function() { return _('worker_class = "gthread"', E.speeds.s); }).then(n);
    p = p.then(function() { return _('threads = 4', E.speeds.s); }).then(n);
    p = p.then(function() { return w(100); });
    p = p.then(n);

    p = p.then(function() { return _('timeout = 120', E.speeds.s); }).then(n);
    p = p.then(function() { return _('keepalive = 5', E.speeds.s); }).then(n);
    p = p.then(function() { return _('max_requests = 1000', E.speeds.s); }).then(n);
    p = p.then(function() { return _('max_requests_jitter = 50', E.speeds.s); }).then(n);
    p = p.then(function() { return w(100); });
    p = p.then(n);

    p = p.then(function() { return _('accesslog = "-"', E.speeds.s); }).then(n);
    p = p.then(function() { return _('errorlog = "-"', E.speeds.s); }).then(n);
    p = p.then(function() { return _('loglevel = "info"', E.speeds.s); }).then(n);
    p = p.then(function() { return w(100); });
    p = p.then(n);

    p = p.then(function() { return _('capture_output = True', E.speeds.s); }).then(n);
    p = p.then(function() { return _('enable_stdio_inheritance = True', E.speeds.s); }).then(n);
    p = p.then(function() { return w(400); });

    p = p.then(function() { E.setCursor(false); E.removeAutocomplete(); return E.showOutput([
        { text: '$ gunicorn wsgi:app', color: 'var(--accent)', delay: 300 },
        { text: '', delay: 60 },
        { text: '[INFO] Starting gunicorn 23.0.0', color: 'var(--text-secondary)', delay: 200 },
        { text: '[INFO] Listening at: http://0.0.0.0:8000', color: '#50fa7b', delay: 300 },
        { text: '[INFO] Using worker: gthread', color: 'var(--text-secondary)', delay: 150 },
        { text: '[INFO] Booting worker with pid: 1234', color: 'var(--text-secondary)', delay: 200 },
        { text: '[INFO] Booting worker with pid: 1235', color: 'var(--text-secondary)', delay: 150 },
        { text: '[INFO] Booting worker with pid: 1236', color: 'var(--text-secondary)', delay: 100 },
        { text: '', delay: 60 },
        { text: '✓ gunicorn ready — 3 workers · 4 threads each', color: '#f1fa8c', delay: 300 },
    ]); });

    return p;
});
