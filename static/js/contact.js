/* The header's Contact control.
   ==============================
   A bare `mailto:` is a correct link that does nothing at all on a machine with
   no mail handler - the click lands, no window opens, and the button reads as
   broken. So the header's Contact keeps the mailto as its no-JavaScript
   fallback and opens this panel when the script is there: the address in
   readable form, a copy control, the mailto for anyone who does have a mail
   app, and a web-compose link that works with neither.

   The trigger stays an `<a href="mailto:...">` rather than a `<button>`: a
   button with no script behind it would be dead, which is worse than the
   problem being fixed. */
(function () {
  "use strict";

  var copiedTimers = new WeakMap();

  function statusFor(button) {
    /* Walk up rather than looking in the immediate parent: the header panel's
       status is a sibling of the actions block, and the contact section's is a
       sibling of the button inside its paragraph. Either way the nearest one is
       the right one, and a `role="status"` that never receives text announces
       nothing. */
    var node = button.parentElement;
    while (node) {
      var found = node.querySelector ? node.querySelector("[data-contact-status]") : null;
      if (found) return found;
      node = node.parentElement;
    }
    return null;
  }

  function feedback(button, text) {
    var status = statusFor(button);
    if (status) status.textContent = text;
    var previous = copiedTimers.get(button);
    if (previous) clearTimeout(previous);
    if (!button.dataset.contactLabel) button.dataset.contactLabel = button.textContent;
    button.textContent = text === "" ? button.dataset.contactLabel : text;
    if (text !== "") {
      copiedTimers.set(
        button,
        setTimeout(function () {
          button.textContent = button.dataset.contactLabel;
          if (status) status.textContent = "";
        }, 1600)
      );
    }
  }

  function bindCopy(button) {
    button.addEventListener("click", function (event) {
      event.preventDefault();
      var value = button.getAttribute("data-copy-value") || "";
      var done = function () { feedback(button, "Copied"); };
      var failed = function () { feedback(button, "Select it"); };
      if (navigator.clipboard && navigator.clipboard.writeText && value) {
        navigator.clipboard.writeText(value).then(done, failed);
      } else {
        failed();
      }
    });
  }

  var copies = document.querySelectorAll("[data-contact-copy]");
  for (var i = 0; i < copies.length; i++) bindCopy(copies[i]);

  var trigger = document.getElementById("ui-contact-trigger");
  var panel = document.getElementById("ui-contact-panel");
  if (!trigger || !panel) return;

  function open() {
    panel.hidden = false;
    trigger.setAttribute("aria-expanded", "true");
  }

  function close() {
    panel.hidden = true;
    trigger.setAttribute("aria-expanded", "false");
  }

  trigger.addEventListener("click", function (event) {
    /* The panel is what answers the click when this script is running; the
       anchor's href remains for the no-JavaScript case and for anyone who
       wants to hand the address to their mail app from the panel anyway. */
    event.preventDefault();
    if (panel.hidden) open();
    else close();
  });

  document.addEventListener("click", function (event) {
    if (!panel.hidden && !panel.contains(event.target) && event.target !== trigger) close();
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") close();
  });
})();
