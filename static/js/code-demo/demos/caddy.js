Demos.register(function() {
    var E = Engine, _ = E.type, n = E.newline, w = E.wait;
    var p = Promise.resolve();
    E.setFilename('Caddyfile');

    function t(s, sp) { return E.stopCheck().then(function() { return _(s, sp || E.speeds.s); }); }

    p = p.then(function() { return _('portfolio.projectnova.download {', E.speeds.m); }).then(n);
    p = p.then(function() { return w(100); });
    p = p.then(function() { return _('    reverse_proxy portfolio_main:7010', E.speeds.s); }).then(n);
    p = p.then(function() { return w(120); });
    p = p.then(n);

    p = p.then(function() { return _('    header /* {', E.speeds.s); }).then(n);
    p = p.then(function() { return _('        X-Frame-Options "SAMEORIGIN"', E.speeds.s); }).then(n);
    p = p.then(function() { return _('        X-Content-Type-Options "nosniff"', E.speeds.s); }).then(n);
    p = p.then(function() { return _('    }', E.speeds.s); }).then(n);
    p = p.then(function() { return w(150); });
    p = p.then(n);

    p = p.then(function() { return _('    handle /api/* {', E.speeds.s); }).then(n);
    p = p.then(function() { return _('        reverse_proxy api:8008', E.speeds.s); }).then(n);
    p = p.then(function() { return _('    }', E.speeds.s); }).then(n);
    p = p.then(function() { return w(100); });
    p = p.then(n);

    p = p.then(function() { return _('    handle /static/* {', E.speeds.s); }).then(n);
    p = p.then(function() { return _('        root * /var/www/static', E.speeds.s); }).then(n);
    p = p.then(function() { return _('        file_server', E.speeds.s); }).then(n);
    p = p.then(function() { return _('    }', E.speeds.s); }).then(n);
    p = p.then(function() { return w(100); });
    p = p.then(n);

    p = p.then(function() { return _('    log {', E.speeds.s); }).then(n);
    p = p.then(function() { return _('        output file /var/log/caddy/portfolio.log', E.speeds.s); }).then(n);
    p = p.then(function() { return _('    }', E.speeds.s); }).then(n);
    p = p.then(function() { return _('}', E.speeds.m); }).then(n);
    p = p.then(function() { return w(400); });

    p = p.then(function() { E.setCursor(false); E.removeAutocomplete(); return E.showOutput([
        { text: '$ caddy reload', color: 'var(--accent)', delay: 300 },
        { text: '', delay: 60 },
        { text: ' ✓ Caddyfile loaded successfully', color: '#50fa7b', delay: 300 },
        { text: ' ✓ Certificate obtained: portfolio.projectnova.download', color: '#50fa7b', delay: 500 },
        { text: ' ✓ Automatic HTTPS enabled', color: '#50fa7b', delay: 200 },
        { text: '', delay: 60 },
        { text: '  → Reverse proxy: portfolio_main:7010', color: 'var(--text-secondary)', delay: 150 },
        { text: '  → Reverse proxy: api:8008', color: 'var(--text-secondary)', delay: 100 },
        { text: '  → File server: /var/www/static', color: 'var(--text-secondary)', delay: 100 },
    ]); });

    return p;
});
