const fs = require("fs");
const path = require("path");
const { DefinePlugin } = require("webpack");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const TerserPlugin = require("terser-webpack-plugin");
const CssMinimizerPlugin = require("css-minimizer-webpack-plugin");
const CopyPlugin = require("copy-webpack-plugin");
const BundleTracker = require("webpack-bundle-tracker");
const { sentryWebpackPlugin } = require("@sentry/webpack-plugin");
const { parse: parseToml } = require("smol-toml");

// Use the same release identifier as the backend Sentry integration
const { version } = parseToml(
  fs.readFileSync(path.resolve(__dirname, "pyproject.toml"), "utf8")
).project;

// Source maps are only generated and uploaded to Sentry if an auth token is set
const sentryUploadEnabled = Boolean(process.env.SENTRY_AUTH_TOKEN);

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
    new DefinePlugin({
      WEBPACK_SENTRY_TRACES_SAMPLE_RATE: JSON.stringify(
        process.env.SENTRY_FRONTEND_TRACES_SAMPLE_RATE || "0.0"
      ),
      WEBPACK_VERSION: JSON.stringify(version),
    }),
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
        // shared chunk) so setWorkerUrl in place-map.ts can point at a real, JS-served file
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
      path: "shared",
    }),
    ...(sentryUploadEnabled
      ? [
          sentryWebpackPlugin({
            org: "digitalfabrik",
            project: "integreat-cms-web",
            authToken: process.env.SENTRY_AUTH_TOKEN,
            url: "https://2d8b10e46b9ac2f1bc17477ec97b4099@sentry.tuerantuer.org//9",
            release: { name: version },
            sourcemaps: {
              // Do not serve the source maps publicly
              filesToDeleteAfterUpload: ["integreat_cms/static/dist/**/*.map"],
            },
            telemetry: false,
          }),
        ]
      : []),
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
  devtool:
    process.env.NODE_ENV !== "production" ? "inline-source-map" : sentryUploadEnabled ? "hidden-source-map" : false,
};
