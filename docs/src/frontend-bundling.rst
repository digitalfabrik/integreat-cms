***************************
Frontend Bundling (Webpack)
***************************

Webpack is being used to generate frontend bundles based on TypeScript code that is compiled to JavaScript as well as SCSS code which is being transpiled to CSS. The following bundles are defined:

1. :github-source:`integreat_cms/static/src/index.ts` (``main.<hash>.js``/``main.<hash>.css``): All main assets (including :ref:`Feature modules`) available on all pages
2. :github-source:`integreat_cms/static/src/editor.ts` (``editor.<hash>.js``): Contains TinyMCE and related assets. It was decided to bundle TinyMCE in a separate file because it is the largest of all bundled assets
3. :github-source:`integreat_cms/static/src/editor_content.ts` (``editor_content.<hash>.js``/``editor_content.<hash>.css``): Contains assets for the TinyMCE content iframe which cannot be passed via the global context
4. :github-source:`integreat_cms/static/src/pdf.ts` (``pdf.<hash>.js``/``pdf.css``): Contains assets for the PDF rendering
5. :github-source:`integreat_cms/static/src/map.ts` (``map.<hash>.js``): Contains maplibre-gl and related assets for the map used in the POI form

To get started with adding new code go to :github-source:`integreat_cms/static/src` and open the bundle you want to edit.
In this file you can import any TypeScript or JavaScript file or library that is needed for the application.
Generated assets will be stored in ``integreat_cms/static/dist``.
When running :github-source:`tools/run.sh`, ``webpack-dev-server`` is being used to generate JavaScript that includes CSS as well as SourceMaps to help debugging the output.
For a production build one should run ``npm run prod``.
This will generate minified js and css files in the same target directory.


Feature modules
===============

Feature modules are very simple components that are scoped to their root element in the DOM.  
They are not bound to a specific template and can be used many times.  

To mark an element as a root for a specific feature module, the attribute ``data-js-<name-of-feature-module>`` needs to be set.  
For example:

.. code-block:: html

    <div data-js-search-query></div>

This sets the div as the root element for the feature module ``search-query``.  

To create a feature module, create a TypeScript file inside ``/integreat_cms/static/src/js/feature/``.
The file name determines the attribute name — ``search-query.ts`` is activated by ``data-js-search-query``.

The file must have a default export with the following signature:

.. code-block:: typescript

    import { defineFeature } from "../utils/define-feature";

    export default defineFeature((root) => {
        // attach event listeners to root or its children
        // do not use document directly
    });


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
* Amharic alphabet: ``Noto Sans Ethiopic``
* Georgian alphabet: ``Noto Sans Georgian``

Unfortunately, xhtml2pdf does not support ``Lateef`` (yet), so at the moment we have to rely on ``DejaVu Sans`` as fallback for the PDF rendering of right-to-left alphabets.
