(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);

  // ---- color helpers -------------------------------------------------

  const hsvToRgb = (h, s, v) => {
    const f = (n) => {
      const k = (n + h / 60) % 6;
      return v - v * s * Math.max(0, Math.min(k, 4 - k, 1));
    };
    return [f(5), f(3), f(1)].map((c) => Math.round(c * 255));
  };

  const rgbToHsv = ([r, g, b]) => {
    r /= 255; g /= 255; b /= 255;
    const max = Math.max(r, g, b), d = max - Math.min(r, g, b);
    let h = 0;
    if (d) {
      if (max === r) h = ((g - b) / d + 6) % 6;
      else if (max === g) h = (b - r) / d + 2;
      else h = (r - g) / d + 4;
      h *= 60;
    }
    return { h, s: max ? d / max : 0, v: max };
  };

  const toHex = (rgb) => "#" + rgb.map((c) => c.toString(16).padStart(2, "0")).join("");
  const fromHex = (hex) => [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16));

  // ---- api -----------------------------------------------------------

  let toastTimer;
  const toast = (msg, error = false) => {
    const el = $("toast");
    el.textContent = msg;
    el.classList.toggle("error", error);
    el.classList.add("show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => el.classList.remove("show"), 2500);
  };

  const api = async (method, path, body) => {
    try {
      const res = await fetch("/api" + path, {
        method,
        headers: body ? { "Content-Type": "application/json" } : {},
        body: body ? JSON.stringify(body) : undefined,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || res.statusText);
      return data;
    } catch (err) {
      toast(err.message === "Failed to fetch" ? "Can't reach the controller" : err.message, true);
      return null;
    }
  };

  // ---- state ---------------------------------------------------------

  const hsv = { h: 30, s: 0.8, v: 1 };
  let on = false;
  let busyUntil = 0; // ignore server color updates while the user is interacting
  let dragging = false;

  const markBusy = () => { busyUntil = Date.now() + 1500; };
  const currentRgb = () => hsvToRgb(hsv.h, hsv.s, hsv.v);

  // ---- color wheel ---------------------------------------------------

  const canvas = $("wheel");
  const ctx = canvas.getContext("2d");
  const cursor = $("cursor");

  const drawWheel = () => {
    const size = Math.round(canvas.getBoundingClientRect().width * (window.devicePixelRatio || 1));
    if (!size || canvas.width === size) return;
    canvas.width = canvas.height = size;
    const img = ctx.createImageData(size, size);
    const r = size / 2;
    for (let y = 0; y < size; y++) {
      for (let x = 0; x < size; x++) {
        const dx = x + 0.5 - r, dy = y + 0.5 - r;
        const dist = Math.hypot(dx, dy);
        const i = (y * size + x) * 4;
        if (dist > r) continue;
        const h = ((Math.atan2(dy, dx) * 180) / Math.PI + 360) % 360;
        const [R, G, B] = hsvToRgb(h, Math.min(dist / r, 1), 1);
        img.data[i] = R; img.data[i + 1] = G; img.data[i + 2] = B;
        // soft edge
        img.data[i + 3] = Math.min(255, (r - dist) * 255);
      }
    }
    ctx.putImageData(img, 0, 0);
  };

  const placeCursor = () => {
    const rect = canvas.getBoundingClientRect();
    const r = rect.width / 2;
    const a = (hsv.h * Math.PI) / 180;
    cursor.style.left = r + Math.cos(a) * hsv.s * r + "px";
    cursor.style.top = r + Math.sin(a) * hsv.s * r + "px";
    cursor.style.background = toHex(hsvToRgb(hsv.h, hsv.s, 1));
  };

  const pick = (e) => {
    const rect = canvas.getBoundingClientRect();
    const r = rect.width / 2;
    const dx = e.clientX - rect.left - r, dy = e.clientY - rect.top - r;
    hsv.h = ((Math.atan2(dy, dx) * 180) / Math.PI + 360) % 360;
    hsv.s = Math.min(Math.hypot(dx, dy) / r, 1);
    changed();
  };

  canvas.addEventListener("pointerdown", (e) => {
    dragging = true;
    canvas.setPointerCapture(e.pointerId);
    pick(e);
  });
  canvas.addEventListener("pointermove", (e) => dragging && pick(e));
  const endDrag = () => { dragging = false; };
  canvas.addEventListener("pointerup", endDrag);
  canvas.addEventListener("pointercancel", endDrag);

  const brightness = $("brightness");
  brightness.addEventListener("input", () => {
    hsv.v = brightness.value / 100;
    changed();
  });

  // Throttled sending: at most one request in flight, always ends on the latest color.
  let sending = false, pending = false;
  const send = async () => {
    if (sending) { pending = true; return; }
    sending = true;
    do {
      pending = false;
      const state = await api("POST", "/color", { color: toHex(currentRgb()) });
      if (state) { on = state.on; renderPower(); }
    } while (pending);
    sending = false;
  };

  const changed = () => {
    markBusy();
    on = true;
    renderColor();
    renderPower();
    send();
  };

  // ---- rendering -----------------------------------------------------

  const setCurrent = (hex) => {
    document.documentElement.style.setProperty("--current", hex);
  };

  const renderColor = () => {
    const hex = toHex(currentRgb());
    $("current-hex").textContent = hex;
    $("current-swatch").style.background = hex;
    $("brightness-val").textContent = Math.round(hsv.v * 100) + "%";
    brightness.value = Math.round(hsv.v * 100);
    brightness.style.setProperty(
      "--track",
      `linear-gradient(90deg, #000, ${toHex(hsvToRgb(hsv.h, hsv.s, 1))})`
    );
    placeCursor();
    renderFavMarks();
  };

  const renderPower = () => {
    $("power").setAttribute("aria-pressed", String(on));
    document.body.classList.toggle("off", !on);
  };

  // ---- tabs ----------------------------------------------------------

  const showTab = (name) => {
    document.querySelectorAll(".tabs button").forEach((b) =>
      b.classList.toggle("active", b.dataset.tab === name)
    );
    document.querySelectorAll(".panel").forEach((p) => (p.hidden = p.id !== "panel-" + name));
    if (name === "static") { drawWheel(); placeCursor(); }
  };

  document.querySelectorAll(".tabs button").forEach((b) =>
    b.addEventListener("click", () => showTab(b.dataset.tab))
  );

  // ---- fade / rainbow ------------------------------------------------

  const fmtSeconds = (s) => (s < 60 ? `${s}s` : `${Math.floor(s / 60)}m ${s % 60 ? (s % 60) + "s" : ""}`.trim());

  const bindPeriod = (inputId, labelId) => {
    const input = $(inputId);
    const update = () => ($(labelId).textContent = fmtSeconds(Number(input.value)));
    input.addEventListener("input", update);
    update();
  };
  bindPeriod("fade-period", "fade-period-val");
  bindPeriod("rainbow-period", "rainbow-period-val");

  $("fade-go").addEventListener("click", async () => {
    const state = await api("POST", "/fade", {
      start: $("fade-a").value,
      end: $("fade-b").value,
      period: Number($("fade-period").value),
    });
    if (state) { on = state.on; renderPower(); }
  });

  $("rainbow-go").addEventListener("click", async () => {
    const state = await api("POST", "/rainbow", { period: Number($("rainbow-period").value) });
    if (state) { on = state.on; renderPower(); }
  });

  // ---- effects -------------------------------------------------------

  document.querySelectorAll(".effect").forEach((btn) =>
    btn.addEventListener("click", async () => {
      const name = btn.dataset.effect;
      const body = { name };
      if (name === "strobe") body.rate = Number($("strobe-rate").value);
      const state = await api("POST", "/effect", body);
      if (state) { on = state.on; renderPower(); markEffect(state.mode); }
    })
  );

  const strobeRate = $("strobe-rate");
  const showStrobeRate = () => ($("strobe-rate-val").textContent = strobeRate.value + "/s");
  strobeRate.addEventListener("input", showStrobeRate);
  strobeRate.addEventListener("change", () => {
    // Apply a new speed right away if the strobe is already running.
    if (document.querySelector('.effect[data-effect="strobe"]').classList.contains("active")) {
      document.querySelector('.effect[data-effect="strobe"]').click();
    }
  });
  showStrobeRate();

  const markEffect = (mode) =>
    document.querySelectorAll(".effect").forEach((b) =>
      b.classList.toggle("active", mode.type === "effect" && mode.name === b.dataset.effect)
    );

  // ---- power ---------------------------------------------------------

  $("power").addEventListener("click", async () => {
    on = !on;
    renderPower();
    markBusy();
    const state = await api("POST", "/power", { on });
    if (state) { on = state.on; renderPower(); }
  });

  // ---- favorites -----------------------------------------------------

  let favorites = [];
  let editing = false;

  const renderFavs = () => {
    const box = $("favs");
    box.classList.toggle("editing", editing);
    $("edit-favs").textContent = editing ? "Done" : "Edit";
    box.replaceChildren();
    if (!favorites.length) {
      const p = document.createElement("span");
      p.className = "empty";
      p.textContent = "Nothing saved yet. Pick a color and tap ♥ Save.";
      box.append(p);
    }
    for (const hex of favorites) {
      const b = document.createElement("button");
      b.className = "fav";
      b.style.background = hex;
      b.setAttribute("aria-label", hex);
      const x = document.createElement("span");
      x.className = "x";
      x.textContent = "×";
      b.append(x);
      b.addEventListener("click", async () => {
        if (editing) {
          const list = await api("DELETE", "/favorites/" + hex.slice(1));
          if (list) { favorites = list; renderFavs(); }
        } else {
          Object.assign(hsv, rgbToHsv(fromHex(hex)));
          showTab("static");
          changed();
        }
      });
      box.append(b);
    }
  };

  const renderFavMarks = () => {
    $("save-fav").textContent = favorites.includes(toHex(currentRgb())) ? "♥ Saved" : "♡ Save";
  };

  $("save-fav").addEventListener("click", async () => {
    const list = await api("POST", "/favorites", { color: toHex(currentRgb()) });
    if (list) { favorites = list; renderFavs(); renderFavMarks(); toast("Saved to favorites"); }
  });

  $("edit-favs").addEventListener("click", () => { editing = !editing; renderFavs(); });

  // ---- sync with server ----------------------------------------------

  let mockMode = false;
  let syncTimer;
  const enableMockPreview = () => {
    mockMode = true;
    const strip = $("strip");
    for (let i = 0; i < 24; i++) strip.append(document.createElement("i"));
    $("strip-preview").hidden = false;
    // Poll fast so fades and rainbow look smooth in the preview.
    document.documentElement.style.setProperty("--glow-speed", "0.1s");
    clearInterval(syncTimer);
    syncTimer = setInterval(sync, 100);
  };

  let firstSync = true;
  const sync = async () => {
    const state = await api("GET", "/state");
    if (!state) return;
    setCurrent(state.color);
    if (state.mock && !mockMode) enableMockPreview();
    if (!dragging && Date.now() > busyUntil) {
      on = state.on;
      renderPower();
      const mode = state.mode;
      markEffect(mode);
      if (mode.type === "static") {
        Object.assign(hsv, rgbToHsv(fromHex(mode.color)));
        renderColor();
      }
      if (firstSync) {
        showTab(mode.type === "effect" ? "effects" : mode.type);
        if (mode.type === "fade") {
          $("fade-a").value = mode.colors[0];
          $("fade-b").value = mode.colors[1];
          $("fade-period").value = mode.period;
          $("fade-period").dispatchEvent(new Event("input"));
        } else if (mode.type === "effect" && mode.rate) {
          strobeRate.value = mode.rate;
          showStrobeRate();
        } else if (mode.type === "rainbow") {
          $("rainbow-period").value = mode.period;
          $("rainbow-period").dispatchEvent(new Event("input"));
        }
      }
    }
    firstSync = false;
  };

  // ---- init ----------------------------------------------------------

  window.addEventListener("resize", () => { drawWheel(); placeCursor(); });
  renderColor();
  renderPower();
  drawWheel();
  api("GET", "/favorites").then((list) => { if (list) { favorites = list; renderFavs(); renderFavMarks(); } });
  sync();
  syncTimer = setInterval(sync, 1000);
})();
