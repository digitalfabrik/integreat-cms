***************************
Frontend Bundling (Webpack)
***************************

Webpack is being used to generate frontend bundles based on TypeScript code that is compiled to JavaScript as well as SCSS code which is being transpiled to CSS. The following bundles are defined:

1. :github-source:`integreat_cms/static/src/index.ts` (``main.<hash>.js``/``main.<hash>.css``): All main assets (including :ref:`Feature modules <feature-modules>`) available on all pages
2. :github-source:`integreat_cms/static/src/editor.ts` (``editor.<hash>.js``): Contains TinyMCE and related assets. It was decided to bundle TinyMCE in a separate file because it is the largest of all bundled assets
3. :github-source:`integreat_cms/static/src/editor_content.ts` (``editor_content.<hash>.js``/``editor_content.<hash>.css``): Contains assets for the TinyMCE content iframe which cannot be passed via the global context
4. :github-source:`integreat_cms/static/src/pdf.ts` (``pdf.<hash>.js``/``pdf.css``): Contains assets for the PDF rendering
5. :github-source:`integreat_cms/static/src/map.ts` (``map.<hash>.js``): Contains maplibre-gl and related assets for the map used in the place form

To get started with adding new code go to :github-source:`integreat_cms/static/src` and open the bundle you want to edit.
In this file you can import any TypeScript or JavaScript file or library that is needed for the application.
Generated assets will be stored in ``integreat_cms/static/dist``.
When running :github-source:`tools/run.sh`, ``webpack-dev-server`` is being used to generate JavaScript that includes CSS as well as SourceMaps to help debugging the output.
For a production build one should run ``npm run prod``.
This will generate minified js and css files in the same target directory.

.. _frontend-sentry:

Error monitoring (Sentry)
=========================

All bundles import :github-source:`integreat_cms/static/src/js/sentry.ts`, which initializes Sentry error reporting and performance tracing.
The configuration is injected at build time via environment variables, so they have to be set when running ``npm run prod``:

* ``SENTRY_FRONTEND_DSN``: The DSN of the Sentry project for the frontend. If this is not set, Sentry is disabled and not included in the bundles.
* ``SENTRY_FRONTEND_ENVIRONMENT``: The environment which is reported to Sentry (defaults to ``production`` for production builds and ``development`` otherwise)
* ``SENTRY_FRONTEND_TRACES_SAMPLE_RATE``: The percentage of transactions which are sent to Sentry for performance tracing (defaults to ``0.0``)

The release is set to ``integreat-cms@<version>``, the same as in the backend. No personally identifiable information is sent to Sentry.

To upload source maps to Sentry, additionally set the following variables:

* ``SENTRY_AUTH_TOKEN``: An auth token for Sentry. If this is not set, no source maps are generated or uploaded.
* ``SENTRY_ORG``: The slug of the Sentry organization
* ``SENTRY_PROJECT``: The slug of the Sentry project
* ``SENTRY_URL``: The URL of the Sentry instance (only needed for self-hosted Sentry)

The source maps are deleted after the upload, so they are not served publicly.

.. _feature-modules:

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

.. note::

    Because feature modules are loaded once and cached, **module-level variables are shared across all instances** of the same module on a page.
    Any state that belongs to a single instance (e.g. counters, timer IDs, DOM references) must be declared inside the default export function, not at module level.

.. note::

    **Feature modules may only import from** ``js/utils/``.
    They must not import from other feature modules, and no code outside ``js/feature/`` should import from a feature module.
    Any logic that needs to be shared between a feature module and other code belongs in ``js/utils/`` instead.

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

The PDF export uses the same fonts, which are defined in the separate ``*-pdf.css`` files:

* Headings and table of contents of latin alphabets: ``Raleway``
* Latin alphabets: ``Open Sans``
* Right-to-left alphabets: ``Lateef``
* Chinese alphabet: ``Noto Sans SC``
* Amharic alphabet: ``Noto Sans Ethiopic``
* Georgian alphabet: ``Noto Sans Georgian``
* Fallback for latin and right-to-left alphabets: ``DejaVu Sans``
