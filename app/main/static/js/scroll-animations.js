document.addEventListener('DOMContentLoaded', () => {
  const io = new IntersectionObserver((entries, ob) => {
    entries.forEach(e => {
      if (!e.isIntersecting) return;

      const el    = e.target;
      const type  = el.dataset.animate || 'fade-up';
      const delay = el.dataset.delay   || '0';

      el.style.animationDelay = `${delay}s`;
      el.classList.add(`animate-${type}`);
      ob.unobserve(el);
    });
  }, { threshold: 0.12 });

  document.querySelectorAll('[data-animate]').forEach(el => io.observe(el));
});