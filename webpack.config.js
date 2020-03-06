const path = require("path");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const TerserPlugin = require("terser-webpack-plugin");
const CssMinimizerPlugin = require("css-minimizer-webpack-plugin");
const CopyPlugin = require("copy-webpack-plugin");

module.exports = {
  entry: {
    main: "./src/frontend/index.ts",
    editor: "./src/frontend/editor.ts", // This contains resources required for the editor UI
    editor_content: "./src/frontend/editor_content.ts", // This contains resources for the editor content iframe
    pdf: "./src/frontend/pdf.ts"
  },
  output: {
    filename: "[name].js",
    path: path.resolve(__dirname, "src/cms/static"),
  },
  module: {
    rules: [
      {
        test: /\.s[ac]ss$/i,
        use: [
          process.env.NODE_ENV !== "production"
            ? "style-loader"
            : MiniCssExtractPlugin.loader,
          "css-loader",
          "postcss-loader",
          "sass-loader",
        ],
      },
      {
        test: /\.css$/i,
        use: [
          MiniCssExtractPlugin.loader,
          "css-loader",
          "postcss-loader",
        ],
      },
      {
        test: /\.tsx?$/,
        use: [
          {
            loader: "babel-loader",
            options: {
              presets: ["@babel/preset-env"],
            },
          },
          "ts-loader",
        ],
        exclude:  /node_modules/,
      },
      {
        test: /\.jsx?$/,
        use: [
          {
            loader: "babel-loader",
            options: {
              presets: ["@babel/preset-env"],
            },
          }
        ],
        exclude: /node_modules\/(?!chart\.js|htmldiff-js)/,
      },
      {
        test: /\.(woff(2)?|ttf|eot|otf)(\?v=[0-9]\.[0-9]\.[0-9])?$/,
        loader: "file-loader",
        options: {
          name: "fonts/[name].[hash].[ext]",
          publicPath: "/static/",
        },
      },
      {
        test: /\.(png|jpg|gif|svg)$/i,
        loader: "url-loader",
        options: {
          limit: 8192,
        },
      },
    ],
  },
  resolve: {
    extensions: [".tsx", ".ts", ".js"],
  },
  plugins: [
    new MiniCssExtractPlugin({
      filename: "[name].css",
      chunkFilename: "[id].css",
    }),
    new CopyPlugin({
      patterns: [
        { from: "node_modules/tinymce/skins/ui/oxide/skin.min.css", to: "skins/ui/oxide/skin.min.css" },
        { from: "node_modules/tinymce/skins/ui/oxide/content.min.css", to: "skins/ui/oxide/content.min.css" },
        { from: "src/frontend/svg", to: "svg" },
        { from: "src/frontend/images", to: "images" },
      ],
    }),
  ],
  optimization: {
    minimize: process.env.NODE_ENV === "production",
    minimizer: [new TerserPlugin(), new CssMinimizerPlugin()],
  },
  devtool: process.env.NODE_ENV !== "production" ? "inline-source-map" : false,
  devServer: {
    contentBase: path.resolve(__dirname, "src/cms/static"),
    compress: true,
    port: 9000,
    writeToDisk: true,
  },
};
