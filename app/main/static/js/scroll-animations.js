document.addEventListener('DOMContentLoaded', () => {
  const opts   = { threshold: 0.12 };
  const unveil = (entries, observer) => {
    entries.forEach(entry => {
      if (!entry.isIntersecting) return;

      const el      = entry.target;
      const type    = el.dataset.animate || 'fade-up';
      const delay   = el.dataset.delay || '0';

      el.style.animationDelay = `${delay}s`;
      el.classList.add(`animate-${type}`);

      observer.unobserve(el);
    });
  };

  const io = new IntersectionObserver(unveil, opts);
  document
    .querySelectorAll('[data-animate]')
    .forEach(el => io.observe(el));
});