/**
 * ====================================================================
 * VALORA AI — 3D ACOUSTIC ENVIRONMENT CANVAS ENGINE
 * Floating vocal cord ribbons, reactive frequency particles,
 * mouse parallax & RGB chromatic edge dispersion.
 * ====================================================================
 */

(function () {
  const canvas = document.getElementById("valora-acoustic-canvas");
  if (!canvas) return;

  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  let width = window.innerWidth;
  let height = window.innerHeight;
  let dpr = Math.min(window.devicePixelRatio || 1, 2);

  const mouse = { x: width / 2, y: height / 2, targetX: width / 2, targetY: height / 2, vx: 0, vy: 0 };
  let scrollY = window.scrollY;
  let targetScrollY = window.scrollY;
  let time = 0;

  // ------------------------------------------------------------------
  // 1. Acoustic Particles Entity System
  // ------------------------------------------------------------------
  const NUM_PARTICLES = 140;
  const particles = [];
  for (let i = 0; i < NUM_PARTICLES; i++) {
    particles.push({
      x: (Math.random() - 0.5) * 2200,
      y: (Math.random() - 0.5) * 2200,
      z: Math.random() * 1200 + 50,
      baseZ: Math.random() * 1200 + 50,
      size: Math.random() * 2.2 + 0.6,
      vx: (Math.random() - 0.5) * 0.5,
      vy: (Math.random() - 0.5) * 0.4 - 0.25, // Anti-gravity upward drift
      alpha: Math.random() * 0.5 + 0.2,
      phase: Math.random() * Math.PI * 2,
    });
  }

  // ------------------------------------------------------------------
  // 2. 3D Vocal Cord Acoustic Ribbons
  // ------------------------------------------------------------------
  const ribbons = [
    { points: 64, radius: 290, speed: 0.0009, height: 180, color: "rgba(59, 130, 246, 0.32)", fill: "rgba(59, 130, 246, 0.025)" },
    { points: 64, radius: 390, speed: -0.0007, height: 260, color: "rgba(6, 182, 212, 0.24)", fill: "rgba(6, 182, 212, 0.02)" },
    { points: 48, radius: 490, speed: 0.0005, height: 350, color: "rgba(248, 250, 252, 0.12)", fill: "none" },
  ];

  // Shockwaves array
  const shockwaves = [];

  function resize() {
    width = window.innerWidth;
    height = window.innerHeight;
    dpr = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.floor(width * dpr);
    canvas.height = Math.floor(height * dpr);
    canvas.style.width = width + "px";
    canvas.style.height = height + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function project(x, y, z, cx = width / 2, cy = height / 2, fov = 680) {
    const scale = fov / (fov + z);
    return {
      x: cx + x * scale,
      y: cy + y * scale,
      scale,
      visible: z > -fov + 10,
    };
  }

  function rotatePoint(x, y, z, rx, ry, rz) {
    let y1 = y * Math.cos(rx) - z * Math.sin(rx);
    let z1 = y * Math.sin(rx) + z * Math.cos(rx);

    let x2 = x * Math.cos(ry) + z1 * Math.sin(ry);
    let z2 = -x * Math.sin(ry) + z1 * Math.cos(ry);

    let x3 = x2 * Math.cos(rz) - y1 * Math.sin(rz);
    let y3 = x2 * Math.sin(rz) + y1 * Math.cos(rz);

    return { x: x3, y: y3, z: z2 };
  }

  function render(now) {
    time = now * 0.001;

    // Smooth inertia mouse tracking
    const prevMx = mouse.x;
    const prevMy = mouse.y;
    mouse.x += (mouse.targetX - mouse.x) * 0.06;
    mouse.y += (mouse.targetY - mouse.y) * 0.06;
    mouse.vx = mouse.x - prevMx;
    mouse.vy = mouse.y - prevMy;

    // Smooth scroll interpolation
    scrollY += (targetScrollY - scrollY) * 0.08;

    const mouseNormX = (mouse.x / width - 0.5) * 2;
    const mouseNormY = (mouse.y / height - 0.5) * 2;

    ctx.clearRect(0, 0, width, height);

    // Deep luxury dark gradient
    const bgGrd = ctx.createRadialGradient(
      width / 2 + mouseNormX * 70,
      height / 2 + mouseNormY * 70,
      100,
      width / 2,
      height / 2,
      Math.max(width, height) * 0.9
    );
    bgGrd.addColorStop(0, "rgba(7, 10, 15, 0.45)");
    bgGrd.addColorStop(0.6, "rgba(4, 6, 10, 0.85)");
    bgGrd.addColorStop(1, "rgba(0, 0, 0, 0.98)");
    ctx.fillStyle = bgGrd;
    ctx.fillRect(0, 0, width, height);

    // Architectural subtle wireframe grid
    ctx.strokeStyle = "rgba(255, 255, 255, 0.02)";
    ctx.lineWidth = 1;
    const gridStep = 90;
    const gridOffsetY = (scrollY * 0.18) % gridStep;
    for (let x = 0; x < width; x += gridStep) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }
    for (let y = gridOffsetY; y < height; y += gridStep) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }

    // ----------------------------------------------------------------
    // Render Particles
    // ----------------------------------------------------------------
    for (let i = 0; i < NUM_PARTICLES; i++) {
      const p = particles[i];
      p.phase += 0.018;
      p.x += p.vx + Math.sin(p.phase) * 0.35;
      p.y += p.vy - 0.25;

      const dx = (p.x + width / 2) - mouse.x;
      const dy = (p.y + height / 2) - mouse.y;
      const dist = Math.sqrt(dx * dx + dy * dy);
      if (dist < 190 && dist > 0) {
        const force = (1 - dist / 190) * 8;
        p.x += (dx / dist) * force;
        p.y += (dy / dist) * force;
      }

      if (p.y < -1100) p.y = 1100;
      if (p.x < -1100) p.x = 1100;
      if (p.x > 1100) p.x = -1100;

      const proj = project(p.x, p.y + scrollY * 0.35, p.z - 200);
      if (proj.visible && proj.x >= 0 && proj.x <= width && proj.y >= 0 && proj.y <= height) {
        const alpha = p.alpha * proj.scale;
        ctx.fillStyle = `rgba(147, 197, 253, ${Math.min(1, alpha)})`;
        ctx.beginPath();
        ctx.arc(proj.x, proj.y, p.size * proj.scale, 0, Math.PI * 2);
        ctx.fill();
      }
    }

    // ----------------------------------------------------------------
    // Render 3D Vocal Cord Ribbons
    // ----------------------------------------------------------------
    const ribbonCenterX = width / 2 + mouseNormX * 45;
    const ribbonCenterY = height * 0.42 - scrollY * 0.4 + mouseNormY * 30;

    ribbons.forEach((ribbon, rIdx) => {
      const rotX = time * 0.16 + mouseNormY * 0.45 + rIdx * 0.8;
      const rotY = time * 0.24 + mouseNormX * 0.65 + rIdx * 0.6;
      const rotZ = Math.sin(time * 0.1 + rIdx) * 0.2;

      const upperPts = [];
      const lowerPts = [];

      for (let i = 0; i <= ribbon.points; i++) {
        const u = (i / ribbon.points) * Math.PI * 2;
        const wave = Math.sin(u * 3 + time * 2.2) * (ribbon.height * 0.3);
        const radius = ribbon.radius + Math.cos(u * 2 + time * 1.2) * 35;

        const x0 = radius * Math.cos(u);
        const z0 = radius * Math.sin(u);
        const yTop = -ribbon.height * 0.5 + wave;
        const yBot = ribbon.height * 0.5 + wave;

        const pTop = rotatePoint(x0, yTop, z0, rotX, rotY, rotZ);
        const pBot = rotatePoint(x0, yBot, z0, rotX, rotY, rotZ);

        const projTop = project(pTop.x, pTop.y, pTop.z, ribbonCenterX, ribbonCenterY);
        const projBot = project(pBot.x, pBot.y, pBot.z, ribbonCenterX, ribbonCenterY);

        upperPts.push(projTop);
        lowerPts.push(projBot);
      }

      if (ribbon.fill !== "none") {
        ctx.beginPath();
        ctx.moveTo(upperPts[0].x, upperPts[0].y);
        for (let i = 1; i < upperPts.length; i++) {
          ctx.lineTo(upperPts[i].x, upperPts[i].y);
        }
        for (let i = lowerPts.length - 1; i >= 0; i--) {
          ctx.lineTo(lowerPts[i].x, lowerPts[i].y);
        }
        ctx.closePath();
        ctx.fillStyle = ribbon.fill;
        ctx.fill();
      }

      const drawEdge = (pts, strokeStyle) => {
        ctx.beginPath();
        ctx.moveTo(pts[0].x, pts[0].y);
        for (let i = 1; i < pts.length; i++) {
          ctx.lineTo(pts[i].x, pts[i].y);
        }
        ctx.strokeStyle = strokeStyle;
        ctx.lineWidth = 1.3;
        ctx.stroke();
      };

      const chromaticAmt = Math.min(6, Math.abs(mouse.vx) + Math.abs(mouse.vy));
      if (chromaticAmt > 1.2) {
        ctx.save();
        ctx.translate(chromaticAmt * 0.6, 0);
        drawEdge(upperPts, "rgba(59, 130, 246, 0.18)");
        ctx.restore();

        ctx.save();
        ctx.translate(-chromaticAmt * 0.6, 0);
        drawEdge(upperPts, "rgba(6, 182, 212, 0.2)");
        ctx.restore();
      }

      drawEdge(upperPts, ribbon.color);
      drawEdge(lowerPts, "rgba(255, 255, 255, 0.08)");

      ctx.strokeStyle = "rgba(255, 255, 255, 0.04)";
      ctx.lineWidth = 0.8;
      for (let i = 0; i < upperPts.length; i += 4) {
        ctx.beginPath();
        ctx.moveTo(upperPts[i].x, upperPts[i].y);
        ctx.lineTo(lowerPts[i].x, lowerPts[i].y);
        ctx.stroke();
      }
    });

    // ----------------------------------------------------------------
    // Render Shockwaves on Click
    // ----------------------------------------------------------------
    for (let i = shockwaves.length - 1; i >= 0; i--) {
      const sw = shockwaves[i];
      const age = (now - sw.born) / 1000;
      sw.radius = age * 480;
      sw.opacity = Math.max(0, 1 - age * 1.4);

      if (sw.opacity <= 0) {
        shockwaves.splice(i, 1);
        continue;
      }

      ctx.beginPath();
      ctx.arc(sw.x, sw.y, sw.radius, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(59, 130, 246, ${(sw.opacity * 0.45).toFixed(3)})`;
      ctx.lineWidth = 1.6;
      ctx.stroke();

      ctx.beginPath();
      ctx.arc(sw.x, sw.y, sw.radius + 3, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(6, 182, 212, ${(sw.opacity * 0.25).toFixed(3)})`;
      ctx.lineWidth = 0.8;
      ctx.stroke();
    }

    requestAnimationFrame(render);
  }

  // ------------------------------------------------------------------
  // Event Listeners
  // ------------------------------------------------------------------
  window.addEventListener("resize", resize);

  window.addEventListener("mousemove", (e) => {
    mouse.targetX = e.clientX;
    mouse.targetY = e.clientY;
  });

  window.addEventListener("click", (e) => {
    shockwaves.push({
      x: e.clientX,
      y: e.clientY,
      radius: 0,
      opacity: 1,
      born: performance.now(),
    });
  });

  window.addEventListener("scroll", () => {
    targetScrollY = window.scrollY;
  });

  document.addEventListener("DOMContentLoaded", () => {
    const sections = document.querySelectorAll(".cinematic-section");
    const trackerLabel = document.getElementById("nav-section-label");
    const progressFill = document.getElementById("scroll-progress-bar");

    window.addEventListener("scroll", () => {
      const totalH = document.documentElement.scrollHeight - window.innerHeight;
      const progress = totalH > 0 ? window.scrollY / totalH : 0;
      if (progressFill) {
        progressFill.style.width = (progress * 100).toFixed(1) + "%";
      }

      let currentSec = "INTRODUCTION";
      sections.forEach((sec) => {
        const rect = sec.getBoundingClientRect();
        if (rect.top <= height * 0.5 && rect.bottom >= height * 0.2) {
          currentSec = sec.getAttribute("data-label") || currentSec;
        }
      });

      if (trackerLabel) {
        trackerLabel.textContent = currentSec;
      }
    });
  });

  resize();
  requestAnimationFrame(render);
})();
