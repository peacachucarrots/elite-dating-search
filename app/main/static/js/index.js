/* static/js/index.js */
/* -----------------------  GLIDE carousels  ----------------------- */
document.addEventListener('DOMContentLoaded', () => {
  /* Testimonials */
  const glideTestimonials = document.querySelector('.glide--testimonials');
  if (glideTestimonials) {
    new Glide(glideTestimonials, {
      type: 'carousel',
      perView: 3,
      autoplay: 20,
      animationDuration: 20000,
      animationTimingFunc: 'linear',
      gap: 32,
      hoverpause: false,
      rewind: false 
    }).mount();
  }

  /* Lessons In Love */
  const lessonsCarousel = document.querySelector('.lessons__carousel');
  if (lessonsCarousel) {
    new Glide(lessonsCarousel, {
      type: 'carousel',
      perView: 3,
      breakpoints: { 1024: { perView: 2 }, 640: { perView: 1 } },
      gap: 24
    }).mount();
  }

  /* Signature SVG lazy-fade */
  const sig = document.getElementById('heroSignature');
  if (sig) sig.addEventListener('load', () => sig.classList.add('is-visible'));

  /* Intersection-observer animations */
  const observer = new IntersectionObserver(
    entries => {
      entries.forEach(entry => {
        if (entry.isIntersecting){
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.25 }
  );
  document.querySelectorAll('[data-animate]').forEach(el => observer.observe(el));
});