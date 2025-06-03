document.addEventListener('DOMContentLoaded', () => {
  const obj = document.getElementById('heroSignature');
  if (!obj) return console.warn('heroSignature object not found');

  const init = () => {
    const svg   = obj.contentDocument?.querySelector('svg');
    if (!svg)   return console.warn('SVG not accessible yet');

    const paths = svg.querySelectorAll('path');
    paths.forEach((p, i) => {
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