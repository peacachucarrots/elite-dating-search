// tailwind.config.cjs
module.exports = {
  content: [
    './app/**/*.html',
    './app/**/*.js',
    './app/main/static/css/**/*.{css,scss}',
  ],
  theme: {
    extend: {
      keyframes: {
        'fade-up': {
          '0%':   { opacity: 0, transform: 'translateY(30px)' },
          '100%': { opacity: 1, transform: 'translateY(0)'    },
        },
      },
      animation: {
        // 0.6 s ease, keep final state (`forwards`)
        'fade-up': 'fade-up 0.6s ease forwards',
      },
    },
  },
  plugins: [],
};