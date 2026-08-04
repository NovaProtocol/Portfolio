Demos.register(function() {
    var E = Engine, _ = E.type, n = E.newline, w = E.wait;
    var p = Promise.resolve();
    E.setFilename('terminal');

    function t(s, sp) { return E.stopCheck().then(function() { return _(s, sp || E.speeds.s); }); }

    p = p.then(function() { return _('git checkout -b feat/proxy-auth', E.speeds.m); }).then(n);
    p = p.then(function() { return w(150); });
    p = p.then(function() { return _('git add caddy/Caddyfile caddy/Dockerfile compose.yaml', E.speeds.m); }).then(n);
    p = p.then(function() { return w(120); });
    p = p.then(function() { return _('git commit -m "gate everything behind Caddy forward_auth"', E.speeds.m); }).then(n);
    p = p.then(function() { return w(200); });
    p = p.then(n);

    p = p.then(function() { return _('git push origin feat/proxy-auth', E.speeds.m); }).then(n);
    p = p.then(function() { return w(250); });
    p = p.then(n);

    p = p.then(function() { return _('git log --oneline -5', E.speeds.m); }).then(n);
    p = p.then(function() { return w(400); });

    p = p.then(function() { E.setCursor(false); E.removeAutocomplete(); return E.showOutput([
        { text: '$ git push -u origin feat/proxy-auth', color: 'var(--accent)', delay: 300 },
        { text: '', delay: 60 },
        { text: 'Enumerating objects: 12, done.', color: 'var(--text-secondary)', delay: 200 },
        { text: 'Counting objects: 100% (12/12), done.', color: 'var(--text-secondary)', delay: 150 },
        { text: 'Writing objects: 100% (7/7), 1.2 KiB', color: 'var(--text-secondary)', delay: 300 },
        { text: 'remote: Resolving deltas: 100% (4/4)', color: 'var(--text-secondary)', delay: 150 },
        { text: '', delay: 60 },
        { text: '✓ Branch feat/proxy-auth pushed', color: '#50fa7b', delay: 200 },
        { text: ' → https://github.com/NovaProtocol/Portfolio', color: 'var(--text-secondary)', delay: 150 },
        { text: '', delay: 60 },
        { text: 'Create a PR on GitHub:', color: '#f1fa8c', delay: 300 },
        { text: '  https://github.com/NovaProtocol/Portfolio/pull/new/feat/proxy-auth', color: 'var(--text-secondary)', delay: 200 },
    ]); });

    return p;
});
