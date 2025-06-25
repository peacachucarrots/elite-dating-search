document.addEventListener('DOMContentLoaded', () => {
  const obj = document.getElementById('heroSignature');
  if (!obj) {
    console.warn('heroSignature object not found');
    return;
  }

  const init = () => {
    const svg = obj.contentDocument?.querySelector('svg');
    if (!svg) return;

    svg.querySelectorAll('path').forEach((p, i) => {
      const len = p.getTotalLength();
      p.style.setProperty('--len',   len);
      p.style.setProperty('--delay', `${i * 0.07}s`);
    });
  };

  if (obj.contentDocument) {
    init();
  } else {
    obj.addEventListener('load', init, { once: true });
  }
});