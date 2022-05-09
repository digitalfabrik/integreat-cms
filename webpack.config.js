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
        {
          from: "node_modules/tinymce/skins/ui/oxide/skin.min.css",
          to: "skins/ui/oxide/skin.min.css",
        },
        {
          from: "node_modules/tinymce/skins/ui/oxide/content.min.css",
          to: "skins/ui/oxide/content.min.css",
        },
        { from: "integreat_cms/static/src/svg", to: "svg" },
        { from: "integreat_cms/static/src/images", to: "images" },
        { from: "integreat_cms/static/src/logos", to: "logos" },
      ],
    }),
    new BundleTracker({ filename: "integreat_cms/webpack-stats.json" }),
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
