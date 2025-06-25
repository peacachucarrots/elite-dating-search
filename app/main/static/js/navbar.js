(function () {
  function initScrollEffect() {
    const nav = document.getElementById('siteNav');
    if (!nav) return;

    const heroTrigger = window.innerHeight * 0.9;

    function handleScroll() {
      if (window.scrollY >= heroTrigger) {
        nav.classList.add('scrolled');
      } else {
        nav.classList.remove('scrolled');
      }
    }

    handleScroll();
    window.addEventListener('scroll', handleScroll, { passive: true });
  }

  function initMobileMenu() {
    const btn  = document.getElementById('nav-toggle');
    const menu = document.getElementById('mobile-menu');
    if (!btn || !menu) return;

    btn.addEventListener('click', () => {
      menu.classList.toggle('menu-mobile--open');
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    initScrollEffect();
    initMobileMenu();
  });
})();