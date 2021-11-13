***************************
Frontend Bundling (Webpack)
***************************

Webpack is being used to generate frontend bundles based on TypeScript code that is compiled to JavaScript as well as SCSS code which is being transpiled to CSS. The following bundles are defined:

1. :github-source:`integreat_cms/static/src/index.ts` (``main.js``/``main.css``): All main assets which should be available on all pages
2. :github-source:`integreat_cms/static/src/editor.ts` (``editor.js``): Contains TinyMCE and related assets. It was decided to bundle TinyMCE in a separate file because it is the largest of all bundled assets
3. :github-source:`integreat_cms/static/src/editor_content.ts` (``editor_content.js``/``editor_content.css``): Contains assets for the TinyMCE content iframe which cannot be passed via the global context
4. :github-source:`integreat_cms/static/src/pdf.ts` (``pdf.js``/``pdf.css``): Contains assets for the PDF rendering

To get started with adding new code go to :github-source:`integreat_cms/static/src` and open the bundle you want to edit.
In this file you can import any TypeScript or JavaScript file or library that is needed for the application.
Generated assets will be stored in ``integreat_cms/static/dist``.
When running :github-source:`dev-tools/run.sh`, ``webpack-dev-server`` is being used to generate JavaScript that includes CSS as well as SourceMaps to help debugging the output.
For a production build one should run ``npm run prod``.
This will generate minified js and css files in the same target directory.


Compatible Browsers
===================

We use ``babel-preset-env`` as well als ``postcss-preset-env`` to transpile or polyfill css and js features for supported browsers. :github-source:`.browserslistrc` contains a list of supported browsers (mostly selected by looking at their usage stats and support status).

.. Note::

    At some point IE 11 will probably be removed from that list.


Fonts
=====

For the conventions of fonts to be used for different content languages, see https://wiki.tuerantuer.org/integreat-languages:

* UI/headings: ``Raleway``
* Latin content: ``Open Sans``
* Right-to-left alphabets: ``Lateef``
* Chinese alphabet: ``Noto Sans SC``

Unfortunately, xhtml2pdf does not support ``Lateef`` (yet), so at the moment we have to rely on ``DejaVu Sans`` as fallback for the PDF rendering of right-to-left alphabets.
