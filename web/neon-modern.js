(function () {
  const reduceMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function ensureParticles() {
    if (document.getElementById('neon-cyber-particles') || reduceMotion) return;
    const canvas = document.createElement('canvas');
    canvas.id = 'neon-cyber-particles';
    canvas.style.position = 'fixed';
    canvas.style.inset = '0';
    canvas.style.pointerEvents = 'none';
    canvas.style.zIndex = '1';
    canvas.style.opacity = '0.32';
    document.body.appendChild(canvas);

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const particles = [];
    const maxParticles = Math.min(70, Math.floor(window.innerWidth / 22));

    function resize() {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    }

    function spawn() {
      particles.length = 0;
      for (let i = 0; i < maxParticles; i++) {
        particles.push({
          x: Math.random() * canvas.width,
          y: Math.random() * canvas.height,
          r: Math.random() * 1.8 + 0.5,
          vx: (Math.random() - 0.5) * 0.22,
          vy: (Math.random() - 0.5) * 0.22,
        });
      }
    }

    function tick() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      for (const p of particles) {
        p.x += p.vx;
        p.y += p.vy;
        if (p.x < -4) p.x = canvas.width + 4;
        if (p.x > canvas.width + 4) p.x = -4;
        if (p.y < -4) p.y = canvas.height + 4;
        if (p.y > canvas.height + 4) p.y = -4;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(0, 240, 255, 0.72)';
        ctx.fill();
      }
      requestAnimationFrame(tick);
    }

    resize();
    spawn();
    window.addEventListener('resize', () => {
      resize();
      spawn();
    });
    tick();
  }

  function wireCompanionSync() {
    const quick = document.getElementById('quick-companion-input');
    const main = document.getElementById('companion-input');
    if (!quick || !main) return;

    let lock = false;
    quick.addEventListener('input', () => {
      if (lock) return;
      lock = true;
      main.value = quick.value;
      lock = false;
    });
    main.addEventListener('input', () => {
      if (lock) return;
      lock = true;
      quick.value = main.value;
      lock = false;
    });
  }

  function activateNav() {
    const path = window.location.pathname;
    document.querySelectorAll('.quick-nav a').forEach((a) => {
      if (a.getAttribute('href') === path) {
        a.classList.add('active');
      }
    });
  }

  function init() {
    ensureParticles();
    wireCompanionSync();
    activateNav();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
