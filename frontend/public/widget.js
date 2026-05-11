/**
 * Resolve. — embeddable AI support operator widget.
 *
 * Customer-site install:
 *   <script>
 *     (function(){var d=document,s=d.createElement('script');
 *       s.src='https://app.resolve.app/widget.js';s.async=1;
 *       s.dataset.tenant='acme';s.dataset.publishableKey='rsv_pub_…';
 *       d.head.appendChild(s);})();
 *   </script>
 *
 * Identify the logged-in customer (recommended):
 *   <script>
 *     window.ResolveSettings = {
 *       user_id: 'u_42',
 *       email: 'kira@acme.co',
 *       // HMAC-SHA256 hex of user_id signed with your tenant secret,
 *       // computed server-side. Without this, sessions are anonymous.
 *       user_hmac: '7c1…42b',
 *       context: { order_id: 'SH-29481', plan: 'pro' }
 *     };
 *   </script>
 *
 * Programmatic API (also available before script loads — calls queue):
 *   Resolve('boot',     { user_id, email, user_hmac, context })
 *   Resolve('open',     { context?: {…} })   // pass extra context per-open
 *   Resolve('close')
 *   Resolve('set',      { context: {…} })
 *   Resolve('shutdown')
 *   Resolve('on', 'event', cb)               // 'open'|'close'|'resolved'|'message'
 */
(function () {
  if (window.Resolve && window.Resolve.q) return; // already initialised

  // ---------- stub for early calls (queued) -----------------------------
  var queue = [];
  function stub() {
    queue.push(Array.prototype.slice.call(arguments));
  }
  stub.q = queue;
  window.Resolve = stub;

  // ---------- find loader script + config -------------------------------
  var script = document.currentScript || (function () {
    var ss = document.getElementsByTagName("script");
    for (var i = ss.length - 1; i >= 0; i--) {
      if (ss[i].src && ss[i].src.indexOf("/widget.js") !== -1) return ss[i];
    }
    return null;
  })();
  if (!script) return;

  var tenant = script.dataset.tenant || "";
  var pk     = script.dataset.publishableKey || "";
  var origin = (function () { try { return new URL(script.src).origin; } catch (e) { return ""; } })();
  var defaults = window.ResolveSettings || {};
  if (!tenant || !pk) {
    console.warn("[Resolve] data-tenant + data-publishable-key required");
    return;
  }

  // ---------- constants / DOM scaffolding -------------------------------
  var BLUE = "#1B4DFF", INK = "#0A0A0A";
  var FRAME_W = 380, FRAME_H = 620;

  // Listeners + state
  var listeners = { open: [], close: [], resolved: [], message: [] };
  var state = {
    booted: false,
    visible: false,
    iframeReady: false,
    user: null,        // {user_id, email, user_hmac}
    context: {}
  };

  // Launcher (rendered immediately)
  var launcher = document.createElement("button");
  launcher.setAttribute("aria-label", "Open support");
  launcher.style.cssText = [
    "position:fixed", "right:20px", "bottom:20px",
    "z-index:2147483646",
    "height:48px", "padding:0 14px 0 12px",
    "border:1px solid " + INK, "background:" + INK, "color:#fff",
    "font:500 13.5px/1 ui-sans-serif,system-ui,-apple-system,Segoe UI,sans-serif",
    "letter-spacing:-0.01em", "cursor:pointer",
    "display:inline-flex", "align-items:center", "gap:8px",
    "border-radius:0",
    "transition:background .15s ease, transform .15s ease"
  ].join(";");
  launcher.innerHTML =
    '<span style="display:inline-block;width:8px;height:8px;background:' + BLUE + '"></span>' +
    '<span>Resolve</span>' +
    '<span id="rsv-badge" style="margin-left:6px;font:500 11px/1 ui-monospace,Menlo,monospace;opacity:.7">support</span>';
  launcher.addEventListener("mouseenter", function () { launcher.style.background = BLUE; });
  launcher.addEventListener("mouseleave", function () { launcher.style.background = INK; });

  // Frame container (hidden until first open)
  var frameWrap = document.createElement("div");
  frameWrap.style.cssText = [
    "position:fixed", "right:20px", "bottom:80px",
    "z-index:2147483647",
    "width:" + FRAME_W + "px", "height:" + FRAME_H + "px",
    "max-width:calc(100vw - 24px)", "max-height:calc(100vh - 120px)",
    "border:1px solid " + INK, "background:#fff",
    "display:none",
    "transform:translateY(8px)", "opacity:0",
    "transition:transform .18s ease, opacity .18s ease"
  ].join(";");

  var iframe = null;
  function makeIframe() {
    if (iframe) return iframe;
    iframe = document.createElement("iframe");
    iframe.title = "Resolve support";
    iframe.style.cssText = "width:100%;height:100%;border:0;display:block;background:#fff";
    iframe.allow = "clipboard-write";
    var u = origin + "/embed/" + encodeURIComponent(tenant) +
            "?pk=" + encodeURIComponent(pk);
    iframe.src = u;
    frameWrap.appendChild(iframe);
    return iframe;
  }

  function postToFrame(msg) {
    if (!iframe || !iframe.contentWindow) return;
    iframe.contentWindow.postMessage({ __resolve: true, ...msg }, origin);
  }

  // ---------- public actions --------------------------------------------
  function boot(opts) {
    opts = opts || {};
    state.user = {
      user_id: opts.user_id || defaults.user_id || null,
      email:   opts.email   || defaults.email   || null,
      user_hmac: opts.user_hmac || defaults.user_hmac || null
    };
    state.context = Object.assign({}, defaults.context || {}, opts.context || {}, {
      page_url: location.href, page_title: document.title
    });
    state.booted = true;
    if (state.iframeReady) {
      postToFrame({ type: "boot", user: state.user, context: state.context });
    }
  }

  function set(opts) {
    if (!opts) return;
    if (opts.context) state.context = Object.assign({}, state.context, opts.context);
    if (state.iframeReady) postToFrame({ type: "set", context: state.context });
  }

  function open(opts) {
    if (opts && opts.context) set({ context: opts.context });
    makeIframe();
    frameWrap.style.display = "block";
    // next frame to allow transition
    requestAnimationFrame(function () {
      frameWrap.style.transform = "translateY(0)";
      frameWrap.style.opacity = "1";
    });
    state.visible = true;
    emit("open");
  }

  function close() {
    frameWrap.style.transform = "translateY(8px)";
    frameWrap.style.opacity = "0";
    setTimeout(function () { if (!state.visible) frameWrap.style.display = "none"; }, 200);
    state.visible = false;
    emit("close");
  }

  function shutdown() {
    state = { booted: false, visible: false, iframeReady: false, user: null, context: {} };
    if (iframe) { iframe.remove(); iframe = null; }
    launcher.remove();
    frameWrap.remove();
    window.removeEventListener("message", onMessage);
  }

  function on(event, cb) {
    if (listeners[event]) listeners[event].push(cb);
  }
  function emit(event, payload) {
    (listeners[event] || []).forEach(function (cb) { try { cb(payload); } catch (e) { /* noop */ } });
  }

  // ---------- iframe <-> parent bridge ----------------------------------
  function onMessage(ev) {
    if (ev.origin !== origin) return;
    var d = ev.data;
    if (!d || !d.__resolve) return;
    if (d.type === "ready") {
      state.iframeReady = true;
      if (state.booted) postToFrame({ type: "boot", user: state.user, context: state.context });
    } else if (d.type === "close") {
      close();
    } else if (d.type === "resolved") {
      emit("resolved", d.payload);
    } else if (d.type === "message") {
      emit("message", d.payload);
    } else if (d.type === "size" && d.height) {
      // optional: dynamic resize requests from inside iframe
      var h = Math.max(420, Math.min(window.innerHeight - 120, d.height));
      frameWrap.style.height = h + "px";
    }
  }
  window.addEventListener("message", onMessage);

  // ---------- launcher click toggles open/close -------------------------
  launcher.addEventListener("click", function () {
    if (state.visible) close(); else open();
  });

  // ---------- dispatcher (Resolve('open'), etc.) ------------------------
  var actions = { boot: boot, open: open, close: close, set: set, shutdown: shutdown, on: on };
  function dispatch() {
    var args = Array.prototype.slice.call(arguments);
    var name = args.shift();
    if (!actions[name]) { console.warn("[Resolve] unknown action:", name); return; }
    if (name === "on") return actions.on(args[0], args[1]);
    return actions[name].apply(null, args);
  }
  dispatch.q = []; // hint: replaced stub

  // ---------- mount -----------------------------------------------------
  function mount() {
    document.body.appendChild(launcher);
    document.body.appendChild(frameWrap);
    // replay queued calls
    var pending = queue.slice();
    window.Resolve = dispatch;
    pending.forEach(function (call) { dispatch.apply(null, call); });
    // auto-boot if not done explicitly
    if (!state.booted) boot({});
  }
  if (document.body) mount();
  else document.addEventListener("DOMContentLoaded", mount);
})();
