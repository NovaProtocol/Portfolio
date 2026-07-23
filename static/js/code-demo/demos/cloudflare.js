Demos.register(function() {
    var E = Engine, _ = E.type, n = E.newline, w = E.wait;
    var p = Promise.resolve();
    E.setFilename('config.yml');

    function t(s, sp) { return E.stopCheck().then(function() { return _(s, sp || E.speeds.s); }); }

    p = p.then(function() { return _('version: 3', E.speeds.m); }).then(n);
    p = p.then(function() { return w(60); });
    p = p.then(n);

    p = p.then(function() { return _('tunnels:', E.speeds.m); }).then(n);
    p = p.then(function() { return _('  portfolio:', E.speeds.s); }).then(n);
    p = p.then(function() { return _('    proto: http', E.speeds.s); }).then(n);
    p = p.then(function() { return _('    address: http://portfolio_main:7010', E.speeds.s); }).then(n);
    p = p.then(function() { return w(100); });
    p = p.then(function() { return _('    credentials-file: /home/nova/.cloudflared/portfolio.json', E.speeds.s); }).then(n);
    p = p.then(function() { return w(80); });
    p = p.then(n);

    p = p.then(function() { return _('  gatekeeper:', E.speeds.s); }).then(n);
    p = p.then(function() { return _('    proto: http', E.speeds.s); }).then(n);
    p = p.then(function() { return _('    address: http://gatekeeper:7000', E.speeds.s); }).then(n);
    p = p.then(function() { return _('    credentials-file: /home/nova/.cloudflared/gatekeeper.json', E.speeds.s); }).then(n);
    p = p.then(function() { return w(100); });
    p = p.then(n);

    p = p.then(function() { return _('  waterbillingsystem:', E.speeds.s); }).then(n);
    p = p.then(function() { return _('    proto: http', E.speeds.s); }).then(n);
    p = p.then(function() { return _('    address: http://caddy-gateway:7020', E.speeds.s); }).then(n);
    p = p.then(function() { return _('    credentials-file: /home/nova/.cloudflared/wbs.json', E.speeds.s); }).then(n);
    p = p.then(function() { return w(400); });

    p = p.then(function() { E.setCursor(false); E.removeAutocomplete(); return E.showOutput([
        { text: '$ cloudflared tunnel run portfolio', color: 'var(--accent)', delay: 300 },
        { text: '', delay: 60 },
        { text: '2025/07/23 10:00:01 INF', color: 'var(--text-secondary)', delay: 200 },
        { text: '    Starting tunnel tunnelID=portfolio...', color: 'var(--text-secondary)', delay: 300 },
        { text: '2025/07/23 10:00:02 INF', color: 'var(--text-secondary)', delay: 200 },
        { text: '    Connection registered', color: '#50fa7b', delay: 250 },
        { text: '', delay: 60 },
        { text: '✓ https://portfolio.projectnova.download', color: '#50fa7b', delay: 400 },
        { text: '  → Tunnel active · 3 origins routed', color: 'var(--text-secondary)', delay: 150 },
    ]); });

    return p;
});
