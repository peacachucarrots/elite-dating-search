// tailwind.config.cjs
module.exports = {
  content: [
    './app/**/*.html',
    './app/**/*.js',
    './app/main/static/css/**/*.{css,scss}',
  ],
  theme: {
    extend: {
      keyframes: { },
      spacing: {
        nav: '4rem',
      }
    },
  plugins: [],
  }
};