Demos.register(function() {
    var E = Engine, _ = E.type, n = E.newline, w = E.wait, m = E.moveDown;
    var p = Promise.resolve();
    E.setFilename('app.py');

    function t(s, sp) { return E.stopCheck().then(function() { return _(s, sp || E.speeds.s); }); }

    p = p.then(function() { return _('from flask import Flask, jsonify', E.speeds.m); }).then(n);
    p = p.then(function() { return _('from flask_cors import CORS', E.speeds.m); }).then(n);
    p = p.then(function() { return w(80); });
    p = p.then(n);

    p = p.then(function() { return _('app = Flask(__name__)', E.speeds.s); }).then(n);
    p = p.then(function() { return _('CORS(app)', E.speeds.s); }).then(n);
    p = p.then(function() { return w(60); });
    p = p.then(n);

    p = p.then(function() { return _('@app.route("/api/projects")', E.speeds.m); }).then(n);
    p = p.then(function() { return _('def list_projects():', E.speeds.m); }).then(n);
    p = p.then(function() { return _('    projects = [', E.speeds.s); }).then(n);
    p = p.then(function() { return _('        {"id": 1, "name": "Portfolio", "tech": "Flask"},', E.speeds.s); }).then(n);
    p = p.then(function() { return _('        {"id": 2, "name": "GateKeeper", "tech": "Flask"},', E.speeds.s); }).then(n);
    p = p.then(function() { return _('        {"id": 3, "name": "WaterBilling", "tech": "Flask"},', E.speeds.s); }).then(n);
    p = p.then(function() { return _('    ]', E.speeds.s); }).then(n);
    p = p.then(function() { return _('    return jsonify(projects)', E.speeds.s); }).then(n);
    p = p.then(function() { return w(150); });
    p = p.then(n);

    p = p.then(function() { return _('@app.route("/api/projects/<int:id>")', E.speeds.m); }).then(n);
    p = p.then(function() { return _('def get_project(id):', E.speeds.s); }).then(n);
    p = p.then(function() { return _('    return jsonify({"id": id, "status": "active"})', E.speeds.s); }).then(n);
    p = p.then(function() { return w(200); });
    p = p.then(n);

    p = p.then(function() { return _('if __name__ == "__main__":', E.speeds.s); }).then(n);
    p = p.then(function() { return _('    app.run(host="0.0.0.0", port=5000)', E.speeds.s); }).then(n);
    p = p.then(function() { return w(400); });

    p = p.then(function() { E.setCursor(false); E.removeAutocomplete(); return E.showOutput([
        { text: '$ python app.py', color: 'var(--accent)', delay: 300 },
        { text: '', delay: 60 },
        { text: ' * Serving Flask app "app"', color: 'var(--text-secondary)', delay: 200 },
        { text: ' * Running on http://0.0.0.0:5000', color: '#50fa7b', delay: 300 },
        { text: '', delay: 60 },
        { text: '✓ API ready: 3 routes registered', color: '#f1fa8c', delay: 400 },
    ]); });

    return p;
});
