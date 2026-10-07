/** Tailwind for Portfolio. The palette comes from the CDN design-language kit
 *  (cdn.projectnova.download/flat/dark), exposed here as `ui-*` utilities so
 *  templates share one set of tokens. */
module.exports = {
  content: ["./apps/**/*.html", "./apps/**/*.py"],
  theme: {
    extend: {
      fontFamily: {
        body: ["Inter", "system-ui", "sans-serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", "monospace"],
      },
      colors: {
        ui: {
          surface: "var(--ui-surface)",
          "on-surface": "var(--ui-on-surface)",
          variant: "var(--ui-surface-variant)",
          "on-variant": "var(--ui-on-surface-variant)",
          outline: "var(--ui-outline)",
          primary: "var(--ui-primary)",
          error: "var(--ui-error)",
        },
      },
    },
  },
  plugins: [],
};
