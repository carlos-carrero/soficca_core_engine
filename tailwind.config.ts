import type { Config } from 'tailwindcss';

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        bg: '#090c14',
        panel: '#101728',
        panelSoft: '#151f35',
        accent: '#6ea8fe',
        success: '#2ea48f',
        warning: '#f3aa32',
        danger: '#f87171',
      },
      boxShadow: {
        panel: '0 20px 45px rgba(0,0,0,.35)',
      },
    },
  },
  plugins: [],
};

export default config;
