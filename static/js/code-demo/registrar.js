(function() {
var demos = [];
window.Demos = {
    register: function(fn) { demos.push(fn); },
    getAll: function() { return demos; },
};
})();
