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
    add_key: "./integreat_cms/static/src/js/template/add_key/index.ts",
    content_versions: "./integreat_cms/static/src/js/template/content_versions/index.ts",
    dashboard: "./integreat_cms/static/src/js/template/dashboard/index.ts",
    event_form: "./integreat_cms/static/src/js/template/event_form/index.ts",
    language_form: "./integreat_cms/static/src/js/template/language_form/index.ts",
    languagetreenode_form: "./integreat_cms/static/src/js/template/languagetreenode_form/index.ts",
    page_form: "./integreat_cms/static/src/js/template/page_form/index.ts",
    page_xliff_import_view: "./integreat_cms/static/src/js/template/page_xliff_import_view/index.ts",
    pages_page_tree: "./integreat_cms/static/src/js/template/pages_page_tree/index.ts",
    poi_form: "./integreat_cms/static/src/js/template/poi_form/index.ts",
    poicategory_list: "./integreat_cms/static/src/js/template/poicategory_list/index.ts",
    push_notification_form: "./integreat_cms/static/src/js/template/push_notification_form/index.ts",
    region_form: "./integreat_cms/static/src/js/template/region_form/index.ts",
    translation_coverage: "./integreat_cms/static/src/js/template/translation_coverage/index.ts",
    translations_management: "./integreat_cms/static/src/js/template/translations_management/index.ts",
  },
  output: {
    filename: "[name].[contenthash].js",
    path: path.resolve(__dirname, "integreat_cms/static/dist"),
    clean: true,
    assetModuleFilename: "assets/[name]-[hash][ext][query]",
    chunkFilename: "chunks/[name].[contenthash].js",
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
    splitChunks: {
      chunks: "all",
    },
  },
  devtool: process.env.NODE_ENV !== "production" ? "inline-source-map" : false,
};
