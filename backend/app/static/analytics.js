(() => {
  "use strict";

  if (
    window.top !== window
    || !/^https?:$/.test(location.protocol)
    || navigator.webdriver === true
    || navigator.globalPrivacyControl === true
    || navigator.doNotTrack === "1"
    || window.doNotTrack === "1"
    || document.prerendering === true
  ) {
    return;
  }

  const path = location.pathname || "/";
  let interacted = false;
  let finished = false;
  let visibleMilliseconds = 0;
  let visibleSince = document.visibilityState === "visible"
    ? performance.now()
    : null;

  const currentVisibleMilliseconds = () => (
    visibleMilliseconds
    + (visibleSince === null ? 0 : performance.now() - visibleSince)
  );

  document.addEventListener("visibilitychange", () => {
    const now = performance.now();
    if (document.visibilityState === "visible") {
      visibleSince = now;
    } else if (visibleSince !== null) {
      visibleMilliseconds += now - visibleSince;
      visibleSince = null;
    }
  });

  const noteInteraction = (event) => {
    if (event.isTrusted) interacted = true;
  };
  ["pointerdown", "touchstart", "keydown", "wheel", "scroll"].forEach((name) => {
    window.addEventListener(name, noteInteraction, {
      passive: true,
      once: true,
      capture: true,
    });
  });

  async function postConfirmation(turnstileToken = "") {
    const response = await fetch("/api/analytics/confirm", {
      method: "POST",
      credentials: "same-origin",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        path,
        turnstile_token: turnstileToken,
      }),
    });
    let body = {};
    try {
      body = await response.json();
    } catch (_) {
      body = {};
    }
    return {response, body};
  }

  function loadTurnstile() {
    if (window.turnstile) return Promise.resolve(window.turnstile);
    return new Promise((resolve, reject) => {
      const existing = document.querySelector("script[data-portfolio-turnstile]");
      if (existing) {
        existing.addEventListener("load", () => resolve(window.turnstile), {once: true});
        existing.addEventListener("error", reject, {once: true});
        return;
      }
      const script = document.createElement("script");
      script.src = "https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit";
      script.async = true;
      script.defer = true;
      script.dataset.portfolioTurnstile = "true";
      script.addEventListener("load", () => resolve(window.turnstile), {once: true});
      script.addEventListener("error", reject, {once: true});
      document.head.appendChild(script);
    });
  }

  async function runTurnstile(siteKey, action) {
    const turnstile = await loadTurnstile();
    if (!turnstile || !siteKey) return;

    const container = document.createElement("div");
    container.setAttribute("aria-live", "polite");
    Object.assign(container.style, {
      position: "fixed",
      right: "16px",
      bottom: "16px",
      zIndex: "2147483647",
    });
    document.body.appendChild(container);

    let widgetId;
    const cleanup = () => {
      try {
        if (widgetId !== undefined) turnstile.remove(widgetId);
      } catch (_) {
        // The widget may already have removed itself.
      }
      container.remove();
    };
    widgetId = turnstile.render(container, {
      sitekey: siteKey,
      action,
      appearance: "interaction-only",
      execution: "execute",
      callback: async (token) => {
        try {
          await postConfirmation(token);
        } finally {
          cleanup();
        }
      },
      "error-callback": cleanup,
      "expired-callback": cleanup,
      "timeout-callback": cleanup,
    });
    turnstile.execute(widgetId);
  }

  async function confirmAfterEngagement() {
    if (finished || document.visibilityState !== "visible") return;
    const visibleFor = currentVisibleMilliseconds();
    if (!((interacted && visibleFor >= 3000) || visibleFor >= 8000)) return;
    finished = true;

    try {
      const {response, body} = await postConfirmation();
      if (response.status === 428 && body.detail === "turnstile_required") {
        await runTurnstile(body.site_key, body.action);
      }
    } catch (_) {
      // Analytics must never affect the page or surface noisy console errors.
    }
  }

  const timer = window.setInterval(async () => {
    await confirmAfterEngagement();
    if (finished) window.clearInterval(timer);
  }, 500);
})();
