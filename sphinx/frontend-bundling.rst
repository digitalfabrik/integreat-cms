***************************
Frontend Bundling (Webpack)
***************************

Webpack is being used to generate frontend bundles based on TypeScript code that is compiled to JavaScript as well as SCSS code which is being transpiled to CSS. The following bundles are defined:

1. ``editor.js``/``editor.css``: Contains TinyMCE and related assets. It was decided to bundle TinyMCE in a separate file because it is the largest of all bundled assets
2. ``main.js``/``main.css``: Contains everything else

To get started with adding new code go to :github-source:`src/frontend` and open :github-source:`src/frontend/index.ts` or :github-source:`src/frontend/editor.ts` (depending on the bundle that should be changed).
In this file you can import any TypeScript or JavaScript file or library that is needed for the application.
Generated assets will be stored in ``src/cms/static``. When running :github-source:`dev-tools/run.sh`, `webpack-dev-server` is being used to generate JavaScript that includes CSS as well as SourceMaps to help debugging the output. For a production build one should run ``npm run prod``. This will generate minified js and css files in the same target directory.


Compatible Browsers
===================

We use ``babel-preset-env`` as well als ``postcss-preset-env`` to transpile or polyfill css and js features for supported browsers. :github-source:`.browserslistrc` contains a list of supported browsers (mostly selected by looking at their usage stats and support status).

.. Note::

    At some point IE 11 will probably be removed from that list.
