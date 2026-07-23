(function() {
var codeEl = document.getElementById('typed-code');
var outputLines = document.getElementById('output-lines');
var outputCursor = document.getElementById('output-cursor');
var linesEl = document.getElementById('code-lines');

if (!codeEl) return;

var running = true;
var cursorVisible = true;
var typedLines = [];
var currentLine = 0;
var currentCol = 0;

var PAIRS = { '(': ')' };
var PAIR_OPEN = { ')': '(' };
var autocompleteContainer = null;

var speeds = { q: 10, s: 12, m: 18, f: 24 };
var fileNameEl = document.getElementById('file-name');

function sleep(ms) { return new Promise(function(r) { setTimeout(r, ms); }); }
function setCursor(state) { cursorVisible = state; }

function removeAutocomplete() { if (autocompleteContainer) { autocompleteContainer.remove(); autocompleteContainer = null; } }
function showAutocomplete(items, idx) {
    removeAutocomplete();
    autocompleteContainer = document.createElement('div'); autocompleteContainer.className = 'auto-popup';
    items.forEach(function(item, i) {
        var div = document.createElement('div'); div.className = 'auto-item' + (i === idx ? ' active' : '');
        div.innerHTML = '<span>' + item.label + '</span><span class="kind">' + item.kind + '</span>';
        autocompleteContainer.appendChild(div);
    });
    codeEl.parentElement.appendChild(autocompleteContainer);
    autocompleteContainer.style.top = (codeEl.offsetTop + codeEl.parentElement.scrollTop) + 'px';
    autocompleteContainer.style.left = '40px';
}

function highlight(raw) {
    if (!raw) return '';
    return hljs.highlight(raw, { language: 'python' }).value;
}

function ensureLines(n) { while (typedLines.length < n) typedLines.push(''); }
function getLine(i) { ensureLines(i + 1); return typedLines[i]; }
function setLine(i, v) { ensureLines(i + 1); typedLines[i] = v; }

var MAX_VISIBLE = 20;

function render() {
    var total = typedLines.length;
    var shown = Math.max(total, MAX_VISIBLE);
    var start = total > MAX_VISIBLE ? total - MAX_VISIBLE : 0;

    var html = '<code class="hljs">';
    for (var i = start; i < total; i++) {
        if (i === currentLine && cursorVisible) {
            var before = typedLines[i].slice(0, currentCol);
            var after = typedLines[i].slice(currentCol);
            html += highlight(before) + '<span class="cursor"></span>' + highlight(after);
        } else {
            html += highlight(typedLines[i]);
        }
        if (i < total - 1 || total < MAX_VISIBLE) html += '\n';
    }
    var pad = MAX_VISIBLE - total;
    for (var i = 0; i < pad; i++) {
        html += '\n';
    }
    html += '</code>';
    codeEl.innerHTML = html;

    if (linesEl) {
        var nums = '';
        for (var i = 0; i < MAX_VISIBLE; i++) {
            if (i > 0) nums += '<br>';
            nums += start + i + 1;
        }
        linesEl.innerHTML = nums;
    }
}

function typeChar(ch, spd) {
    var line = getLine(currentLine);
    var pair = PAIRS[ch];
    var skip = PAIR_OPEN[ch];

    if ((skip || ch === '"' || ch === "'") && currentCol < line.length && line[currentCol] === ch) {
        currentCol++;
        render();
        return sleep(spd || 6);
    }

    if (pair || ch === '"' || ch === "'") {
        var close = pair || ch;
        setLine(currentLine, line.slice(0, currentCol) + ch + close + line.slice(currentCol));
        currentCol++;
    } else {
        setLine(currentLine, line.slice(0, currentCol) + ch + line.slice(currentCol));
        currentCol++;
    }

    render();
    return sleep(spd || 6);
}

function typeStr(str, spd) {
    var chain = Promise.resolve();
    var i = 0;
    (function next() {
        if (i >= str.length) return;
        var ch = str[i++];
        chain = chain.then(function() {
            if (!running) return Promise.reject('stopped');
            return typeChar(ch, spd || 6);
        });
        next();
    })();
    return chain;
}

function newline() {
    var line = getLine(currentLine);
    var beforeCursor = line.slice(0, currentCol);
    var afterCursor = line.slice(currentCol);

    setLine(currentLine, beforeCursor);
    typedLines.splice(currentLine + 1, 0, afterCursor);
    currentLine++;
    currentCol = 0;
    render();
    return Promise.resolve();
}

function wait(delay) { return sleep(delay); }

function moveDown() {
    if (currentLine < typedLines.length - 1) {
        currentLine++;
        currentCol = getLine(currentLine).length;
        render();
    }
    return Promise.resolve();
}

function showOutput(lines) {
    outputLines.innerHTML = '';
    outputCursor.style.display = 'none';
    var chain = Promise.resolve();
    lines.forEach(function(entry) {
        chain = chain.then(function() {
            if (!running) return Promise.reject('stopped');
            return sleep(entry.delay || 60).then(function() {
                var div = document.createElement('div');
                div.style.color = entry.color || 'var(--text-secondary)';
                div.textContent = entry.text;
                outputLines.appendChild(div);
            });
        });
    });
    return chain;
}

function clearOutput() { outputLines.innerHTML = ''; outputCursor.style.display = 'none'; }

function clearAll() {
    typedLines = [];
    currentLine = 0; currentCol = 0;
    codeEl.innerHTML = ''; removeAutocomplete();
    render();
}

function setFilename(name) { if (fileNameEl) fileNameEl.textContent = name; }

window.Engine = {
    sleep: sleep,
    setCursor: setCursor,
    removeAutocomplete: removeAutocomplete,
    showAutocomplete: showAutocomplete,
    render: render,
    typeChar: typeChar,
    typeStr: function(str, spd) { return typeStr(str, spd); },
    type: function(str, spd) { return typeStr(str, spd); },
    newline: newline,
    wait: wait,
    moveDown: moveDown,
    showOutput: showOutput,
    clearOutput: clearOutput,
    clearAll: clearAll,
    stopCheck: function() { if (!running) return Promise.reject('stopped'); return Promise.resolve(); },
    speeds: speeds,
    setFilename: setFilename,
};
})();
