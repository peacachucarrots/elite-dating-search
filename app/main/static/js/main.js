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