/**
 * ====================================================================
 * VALORA AI STUDIO — INTERACTIVE KINETIC GRID BACKGROUND
 * Dynamic pointer warp, inertia interpolation, active node glows & click ripples
 * ====================================================================
 */

(function () {
  const canvas = document.getElementById("kinetic-grid-canvas");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const CELL_SIZE = 55;
  const INFLUENCE_RADIUS = 260;
  const MAX_WARP = 24;
  const DOT_SPACING = 28;
  const LERP_SPEED = 0.08;

  const LINE_BASE_DARK = { r: 255, g: 255, b: 255, a: 0.08 };
  const LINE_BASE_LIGHT = { r: 15, g: 23, b: 42, a: 0.06 };
  const NODE_BASE_RADIUS = 1.8;
  const NODE_ACTIVE_RADIUS = 3.2;

  let width = 0;
  let height = 0;
  const mouse = { x: -9999, y: -9999 };
  const targetMouse = { x: -9999, y: -9999 };
  const ripples = [];
  let rafId = null;

  function isDark() {
    return document.documentElement.classList.contains("dark");
  }

  function lerpN(a, b, t) {
    return a + (b - a) * t;
  }

  function lerpColor(base, active, t) {
    const r = Math.round(lerpN(base.r, active.r, t));
    const g = Math.round(lerpN(base.g, active.g, t));
    const b = Math.round(lerpN(base.b, active.b, t));
    const a = lerpN(base.a, active.a, t);
    return `rgba(${r},${g},${b},${a.toFixed(3)})`;
  }

  function resize() {
    width = window.innerWidth;
    height = window.innerHeight;
    const dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.floor(width * dpr);
    canvas.height = Math.floor(height * dpr);
    canvas.style.width = width + "px";
    canvas.style.height = height + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function getWarpedPoint(gx, gy, col, row, cols, rows) {
    const edgeMargin = 1.5;
    const colPin = Math.min(col / edgeMargin, (cols - 1 - col) / edgeMargin, 1);
    const rowPin = Math.min(row / edgeMargin, (rows - 1 - row) / edgeMargin, 1);
    const pinFactor = colPin * colPin * rowPin * rowPin;

    const dx = gx - mouse.x;
    const dy = gy - mouse.y;
    const dist = Math.sqrt(dx * dx + dy * dy);
    const proximity = Math.max(0, 1 - dist / INFLUENCE_RADIUS) * pinFactor;

    let rx = 0;
    let ry = 0;
    for (let i = 0; i < ripples.length; i++) {
      const r = ripples[i];
      const rdx = gx - r.x;
      const rdy = gy - r.y;
      const rdist = Math.sqrt(rdx * rdx + rdy * rdy);
      const waveWidth = 55;
      const diff = rdist - r.radius;
      if (Math.abs(diff) < waveWidth) {
        const strength = (1 - Math.abs(diff) / waveWidth) * r.opacity * 18 * pinFactor;
        const angle = Math.atan2(rdy, rdx);
        const sign = diff < 0 ? -1 : 1;
        rx += Math.cos(angle) * strength * sign * -1;
        ry += Math.sin(angle) * strength * sign * -1;
      }
    }

    if (dist < INFLUENCE_RADIUS && dist > 0 && pinFactor > 0) {
      const t = dist / INFLUENCE_RADIUS;
      const eased = t < 0.01 ? 0 : (1 - t) * (1 - t) * Math.min(1, dist / 60);
      const warpAmt = eased * MAX_WARP * pinFactor;
      const angle = Math.atan2(dy, dx);
      return {
        pt: {
          x: gx - Math.cos(angle) * warpAmt + rx,
          y: gy - Math.sin(angle) * warpAmt + ry,
        },
        proximity,
      };
    }

    return { pt: { x: gx + rx, y: gy + ry }, proximity };
  }

  function draw(now) {
    const darkMode = isDark();
    const lineBase = darkMode ? LINE_BASE_DARK : LINE_BASE_LIGHT;
    const lineActive = darkMode
      ? { r: 59, g: 130, b: 246, a: 0.85 }
      : { r: 37, g: 99, b: 235, a: 0.75 };
    const nodeActive = darkMode
      ? { r: 96, g: 165, b: 250, a: 1.0 }
      : { r: 37, g: 99, b: 235, a: 1.0 };
    const glowColor = darkMode ? "59,130,246" : "37,99,235";
    const rippleColor = darkMode ? "96,165,250" : "37,99,235";
    const dotColor = darkMode ? "rgba(255, 255, 255, 0.04)" : "rgba(15, 23, 42, 0.04)";

    ctx.clearRect(0, 0, width, height);

    // Static ambient background dot matrix
    ctx.fillStyle = dotColor;
    for (let x = DOT_SPACING / 2; x < width; x += DOT_SPACING) {
      for (let y = DOT_SPACING / 2; y < height; y += DOT_SPACING) {
        ctx.beginPath();
        ctx.arc(x, y, 0.7, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    // Update ripples
    for (let i = ripples.length - 1; i >= 0; i--) {
      const r = ripples[i];
      const age = (now - r.born) / 1000;
      r.radius = Math.max(0, age * 400);
      r.opacity = Math.max(0, 1 - age * 1.2);
      if (r.opacity <= 0) {
        ripples.splice(i, 1);
      }
    }

    // Warp grid rows & cols
    const cols = Math.max(2, Math.ceil(width / CELL_SIZE)) + 1;
    const rows = Math.max(2, Math.ceil(height / CELL_SIZE)) + 1;
    const cellW = width / (cols - 1);
    const cellH = height / (rows - 1);

    const pts = [];
    const prox = [];

    for (let row = 0; row < rows; row++) {
      pts[row] = [];
      prox[row] = [];
      for (let col = 0; col < cols; col++) {
        const { pt, proximity } = getWarpedPoint(col * cellW, row * cellH, col, row, cols, rows);
        pts[row][col] = pt;
        prox[row][col] = proximity;
      }
    }

    // Draw grid lines
    const drawSeg = (p1, p2, pr1, pr2) => {
      const avg = (pr1 + pr2) / 2;
      const t = avg * avg * (3 - 2 * avg);
      ctx.beginPath();
      ctx.moveTo(p1.x, p1.y);
      ctx.lineTo(p2.x, p2.y);
      ctx.strokeStyle = lerpColor(lineBase, lineActive, t);
      ctx.lineWidth = lerpN(0.8, 1.5, t);
      ctx.stroke();
    };

    ctx.lineCap = "butt";

    for (let row = 0; row < rows; row++) {
      for (let col = 0; col < cols - 1; col++) {
        drawSeg(pts[row][col], pts[row][col + 1], prox[row][col], prox[row][col + 1]);
      }
    }

    for (let col = 0; col < cols; col++) {
      for (let row = 0; row < rows - 1; row++) {
        drawSeg(pts[row][col], pts[row + 1][col], prox[row][col], prox[row + 1][col]);
      }
    }

    // Draw active nodes with outer glow
    for (let row = 0; row < rows; row++) {
      for (let col = 0; col < cols; col++) {
        const p = pts[row][col];
        const pr = prox[row][col];
        const t = pr * pr * (3 - 2 * pr);
        const r = lerpN(NODE_BASE_RADIUS, NODE_ACTIVE_RADIUS, t);

        if (t > 0.25) {
          const glowR = r + lerpN(0, 6, (t - 0.25) / 0.75);
          const grd = ctx.createRadialGradient(p.x, p.y, r * 0.5, p.x, p.y, glowR);
          grd.addColorStop(0, `rgba(${glowColor},${(t * 0.35).toFixed(3)})`);
          grd.addColorStop(1, `rgba(${glowColor},0)`);
          ctx.beginPath();
          ctx.arc(p.x, p.y, glowR, 0, Math.PI * 2);
          ctx.fillStyle = grd;
          ctx.fill();
        }

        ctx.beginPath();
        ctx.arc(p.x, p.y, r, 0, Math.PI * 2);
        ctx.fillStyle = lerpColor(
          darkMode ? { r: 255, g: 255, b: 255, a: 0.15 } : { r: 15, g: 23, b: 42, a: 0.15 },
          nodeActive,
          t
        );
        ctx.fill();
      }
    }

    // Ripple rings
    for (let i = 0; i < ripples.length; i++) {
      const r = ripples[i];
      const safeRadius = Math.max(0, r.radius);
      ctx.beginPath();
      ctx.arc(r.x, r.y, safeRadius, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(${rippleColor},${(r.opacity * 0.28).toFixed(3)})`;
      ctx.lineWidth = 1.5;
      ctx.stroke();
    }
  }

  function animate(now) {
    mouse.x = lerpN(mouse.x, targetMouse.x, LERP_SPEED);
    mouse.y = lerpN(mouse.y, targetMouse.y, LERP_SPEED);

    draw(now);
    rafId = requestAnimationFrame(animate);
  }

  window.addEventListener("resize", resize);
  window.addEventListener("mousemove", (e) => {
    targetMouse.x = e.clientX;
    targetMouse.y = e.clientY;
    if (mouse.x === -9999) {
      mouse.x = e.clientX;
      mouse.y = e.clientY;
    }
  });

  window.addEventListener("click", (e) => {
    ripples.push({
      x: e.clientX,
      y: e.clientY,
      radius: 0,
      opacity: 1,
      born: performance.now(),
    });
  });

  window.addEventListener("mouseleave", () => {
    targetMouse.x = -9999;
    targetMouse.y = -9999;
  });

  resize();
  rafId = requestAnimationFrame(animate);
})();
