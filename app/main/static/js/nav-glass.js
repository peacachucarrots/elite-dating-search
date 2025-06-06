document.addEventListener('DOMContentLoaded', () => {
  const nav = document.getElementById('siteNav');
  if (!nav) return;

  nav.classList.add('bg-transparent');

  const onScroll = () => {
    const scrolled = window.scrollY > 400;
    nav.classList.toggle('bg-transparent',        !scrolled);
    nav.classList.toggle('bg-neutral-900/60',      scrolled);
    nav.classList.toggle('backdrop-blur-md',       scrolled);
  };

  onScroll();
	window.addEventListener('scroll', onScroll, { passive: true });
});