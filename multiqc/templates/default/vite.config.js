import { resolve } from "path";
const indexBuild = process.env.MQC_INDEX_BUILD === "1";

export default {
  root: resolve(__dirname, "src"),
  build: {
    outDir: "../compiled",
    emptyOutDir: !indexBuild,
    rollupOptions: {
      input: {
        main: resolve(__dirname, indexBuild ? "src/js/bundle-index.js" : "src/js/main.js"),
      },
      output: {
        format: "iife",
        entryFileNames: indexBuild ? "js/bundle-index.js" : "js/multiqc.min.js",
        assetFileNames: "css/multiqc.min.css",
      },
    },
    minify: "terser",
    cssMinify: true,
  },
  css: {
    preprocessorOptions: {
      scss: {
        silenceDeprecations: ["import", "color-functions", "global-builtin", "if-function"],
      },
    },
  },
};
