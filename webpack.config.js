const path = require("path");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const TerserPlugin = require("terser-webpack-plugin");
const CssMinimizerPlugin = require("css-minimizer-webpack-plugin");
const CopyPlugin = require("copy-webpack-plugin");
const BundleTracker = require("webpack-bundle-tracker");

module.exports = {
  entry: {
    main: "./integreat_cms/static/src/index.ts",
    editor: "./integreat_cms/static/src/editor.ts", // This contains resources required for the editor UI
    editor_content: "./integreat_cms/static/src/editor_content.ts", // This contains resources for the editor content iframe
    pdf: "./integreat_cms/static/src/pdf.ts",
    map: "./integreat_cms/static/src/map.ts",
  },
  output: {
    filename: "[name].[contenthash].js",
    path: path.resolve(__dirname, "integreat_cms/static/dist"),
    clean: true,
    assetModuleFilename: "assets/[name]-[hash][ext][query]",
  },
  module: {
    rules: [
      {
        test: /\.s[ac]ss$/i,
        use: [
          process.env.NODE_ENV !== "production" ? "style-loader" : MiniCssExtractPlugin.loader,
          "css-loader",
          "postcss-loader",
          "sass-loader",
        ],
      },
      {
        test: /\.css$/i,
        use: [MiniCssExtractPlugin.loader, "css-loader", "postcss-loader"],
      },
      {
        test: /\.tsx?$/,
        use: [
          {
            loader: "babel-loader",
            options: {
              presets: ["@babel/preset-env"],
              plugins: [
                [
                  "@babel/plugin-transform-react-jsx",
                  {
                    runtime: "classic",
                    pragma: "h",
                    pragmaFrag: "Fragment",
                  },
                ],
              ],
            },
          },
          "ts-loader",
        ],
        exclude: /node_modules/,
      },
      {
        test: /\.jsx?$/,
        use: [
          {
            loader: "babel-loader",
            options: {
              presets: ["@babel/preset-env"],
              plugins: [
                [
                  "@babel/plugin-transform-react-jsx",
                  {
                    runtime: "classic",
                    pragma: "h",
                    pragmaFrag: "Fragment",
                  },
                ],
              ],
            },
          },
        ],
        exclude: /node_modules\/(?!chart\.js|htmldiff-js)/,
      },
      {
        test: /\.(woff(2)?|ttf|eot|otf)(\?v=[0-9]\.[0-9]\.[0-9])?$/,
        type: "asset/resource",
      },
      {
        test: /\.(png|jpg|gif|svg)$/i,
        type: "asset/inline",
      },
    ],
  },
  resolve: {
    extensions: [".tsx", ".ts", ".js"],
    alias: {
      // maplibre-gl v6 is ESM-only; the CommonJS-emitting TS pipeline can't match its exports conditions
      "maplibre-gl$": path.resolve(__dirname, "node_modules/maplibre-gl/dist/maplibre-gl.mjs"),
    },
  },
  plugins: [
    new MiniCssExtractPlugin({
      filename: function (config) {
        if (config.chunk.name == "pdf") return "[name].css";
        else return "[name].[contenthash].css";
      },
      chunkFilename: "[id].[contenthash].css",
    }),
    new CopyPlugin({
      patterns: [
        // maplibre-gl v6 loads its web worker as a separate ES module; ship it (and its
        // shared chunk) so setWorkerUrl in poi-map.ts can point at a real, JS-served file
        {
          from: "node_modules/maplibre-gl/dist/maplibre-gl-worker.mjs",
          to: "maplibre-gl-worker.mjs",
        },
        {
          from: "node_modules/maplibre-gl/dist/maplibre-gl-shared.mjs",
          to: "maplibre-gl-shared.mjs",
        },
        {
          from: "node_modules/tinymce/skins/ui/oxide/skin.css",
          to: "skins/ui/oxide/skin.css",
        },
        {
          from: "node_modules/tinymce/skins/ui/oxide/content.css",
          to: "skins/ui/oxide/content.css",
        },
        { from: "integreat_cms/static/src/svg", to: "svg" },
        { from: "integreat_cms/static/src/images", to: "images" },
        { from: "integreat_cms/static/src/logos", to: "logos" },
      ],
    }),
    new BundleTracker({
      filename: "webpack-stats.json",
      path: "integreat_cms",
    }),
  ],
  optimization: {
    minimize: process.env.NODE_ENV === "production",
    minimizer: [
      new TerserPlugin(),
      new CssMinimizerPlugin({
        exclude: "pdf.css",
      }),
    ],
  },
  devtool: process.env.NODE_ENV !== "production" ? "inline-source-map" : false,
};
