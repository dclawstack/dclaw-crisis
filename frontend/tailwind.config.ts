import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/**/*{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: "#EA580C",
      },
    },
  },
  plugins: [],
};

export default config;
