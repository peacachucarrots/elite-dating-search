/* static/js/main.js */
document.addEventListener('DOMContentLoaded', () => {
  const tGlide = document.querySelector('[data-testid="testimonial-glide"]');
  if (tGlide && window.Glide) {
    new Glide(tGlide, {
      type:       'carousel',
      perView:    1,
      gap:        0,
      autoplay:   6000,
      hoverpause: true
    }).mount();
  }
  });
  
document.addEventListener('scroll', () => {
  const nav = document.querySelector('nav');
  const scrolled = window.scrollY > 400;

  nav.classList.toggle('bg-neutral-900/60',  scrolled);
  nav.classList.toggle('backdrop-blur-md',    scrolled);
});