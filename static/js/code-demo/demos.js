(function() {
var weights = [];

function pickIndex() {
    var demos = Demos.getAll();
    if (demos.length === 0) return -1;

    if (weights.length !== demos.length) {
        weights = demos.map(function() { return 1; });
    }

    var total = 0;
    for (var i = 0; i < weights.length; i++) total += weights[i];

    var r = Math.random() * total;
    for (var i = 0; i < weights.length; i++) {
        r -= weights[i];
        if (r <= 0) return i;
    }
    return weights.length - 1;
}

function startRandom() {
    var demos = Demos.getAll();
    if (demos.length === 0) {
        setTimeout(startRandom, 100);
        return;
    }

    var idx = pickIndex();
    weights[idx] = Math.max(0.1, weights[idx] * 0.3);
    for (var i = 0; i < weights.length; i++) {
        if (i !== idx) weights[i] = Math.min(1, weights[i] + 0.15);
    }

    Engine.clearAll();
    Engine.clearOutput();
    Engine.setCursor(true);

    var p = demos[idx]();

    p.then(function() {
        return Engine.sleep(3000);
    }).then(function() {
        startRandom();
    }).catch(function(err) {
        if (err !== 'stopped') throw err;
    });
}

setTimeout(startRandom, 800);
})();
