module.exports = {
  purge: [],
  darkMode: false, // or 'media' or 'class'
  purge: [
    './src/**/*.html',
    './src/**/*.js',
  ],
  theme: {
    extend: {
      backgroundImage: {
        'icon': "url('/src/frontend/images/integreat-icon.png')",
        'logo': "url('/src/frontend/images/integreat-logo.png')",
        'logo-white': "url('/src/frontend/images/integreat-logo-white.png')",
        'logo-yellow': "url('/src/frontend/images/integreat-logo-yellow.png')",
      },
    },
  },
  variants: {
    extend: {
      backgroundImage: ['hover', 'focus'],
    },
  },
  plugins: [],
}
