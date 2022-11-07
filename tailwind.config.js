const colors = require('tailwindcss/colors')

module.exports = {
  content: [
    './integreat_cms/cms/templates/**/*.html',
    './integreat_cms/static/src/js/**/*.{js,ts,tsx}',
  ],
  safelist: [
    {
      pattern: /(integreat|malte|aschaffenburg)/,
      variants: ['hover'],
    },
  ],
  theme: {
    colors: {
      transparent: 'transparent',
      current: 'currentColor',
      black: colors.black,
      white: colors.white,
      gray: colors.slate,
      red: colors.red,
      orange: colors.orange,
      yellow: colors.yellow,
      green: colors.green,
      blue: colors.blue,
    },
    extend: {
      colors: {
        'water': {
          '50': '#fefeff',
          '100': '#fcfdff',
          '200': '#f8fafe',
          '300': '#f4f7fe',
          '400': '#ecf1fd',
          '500': '#e4ebfc',
          '600': '#cdd4e3',
          '700': '#abb0bd',
          '800': '#898d97',
          '900': '#70737b'
        }
      },
      backgroundImage: {
        'integreat-icon': "url('../logos/integreat/integreat-icon.svg')",
        'integreat-logo': "url('../logos/integreat/integreat-logo-black.svg')",
        'integreat-logo-white': "url('../logos/integreat/integreat-logo-white.svg')",
        'integreat-logo-hover': "url('../logos/integreat/integreat-logo-yellow.svg')",
        'malte-icon': "url('../logos/malte/malte-icon.svg')",
        'malte-logo': "url('../logos/malte/malte-logo-black.svg')",
        'malte-logo-white': "url('../logos/malte/malte-logo-white.svg')",
        'malte-logo-hover': "url('../logos/malte/malte-logo-red.svg')",
        'aschaffenburg-icon': "url('../logos/aschaffenburg/aschaffenburg-icon.svg')",
        'aschaffenburg-logo': "url('../logos/aschaffenburg/aschaffenburg-logo-slate.svg')",
        'aschaffenburg-logo-white': "url('../logos/aschaffenburg/aschaffenburg-logo-white.svg')",
        'aschaffenburg-logo-hover': "url('../logos/aschaffenburg/aschaffenburg-logo-cyan.svg')",
        'border-left': 'linear-gradient(to right, var(--tw-gradient-from), var(--tw-gradient-from) 4px, var(--tw-gradient-to, rgba(0, 0, 0, 0)) 4px)',
      },
      fontFamily: {
        'default': ["Raleway", "Lateef", "Noto Sans SC", "sans-serif"],
        'content': ["Open Sans", "sans-serif"],
        'content-rtl': ["Lateef", "sans-serif"],
        'content-sc': ["Noto Sans SC", "sans-serif"],
      },
      maxHeight: {
        '15': '3.75rem',
        '116': '29rem',
        '160': '40rem',
      },
      gridTemplateColumns: {
        'gallery': 'repeat(auto-fill, minmax(180px, 1fr))',
      },
      width: {
        '120': '30rem',
        '136': '34rem',
        '160': '40rem',
      },
      screens: {
        '3xl': '1700px',
        '4xl': '2100px',
      },
    },
  },
  plugins: [require('@tailwindcss/forms'),],
}
