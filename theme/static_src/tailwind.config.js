module.exports = {
  content: [
    "../templates/**/*.html",
    "../../templates/**/*.html",
    "../../apps/**/templates/**/*.html",
    "../../**/forms.py",
    "../../**/views.py",
  ],
  theme: {
    extend: {},
  },
  plugins: [require("daisyui")],
  daisyui: {
    themes: ["light", "dark", "cupcake"],
  },
}