***************************
Frontend Bundling (Webpack)
***************************

Webpack is being used to generate frontend bundles based on TypeScript code that is compiled to JavaScript as well as SCSS code which is being transpiled to CSS. The following bundles are defined:

1. :github-source:`integreat_cms/static/src/index.ts` (``main.<hash>.js``/``main.<hash>.css``): All main assets (especially feature modules) which should be available on all pages
2. :github-source:`integreat_cms/static/src/editor.ts` (``editor.<hash>.js``): Contains TinyMCE and related assets. It was decided to bundle TinyMCE in a separate file because it is the largest of all bundled assets
3. :github-source:`integreat_cms/static/src/editor_content.ts` (``editor_content.<hash>.js``/``editor_content.<hash>.css``): Contains assets for the TinyMCE content iframe which cannot be passed via the global context
4. :github-source:`integreat_cms/static/src/pdf.ts` (``pdf.<hash>.js``/``pdf.css``): Contains assets for the PDF rendering
5. :github-source:`integreat_cms/static/src/map.ts` (``map.<hash>.js``): Contains maplibre-gl and related assets for the map used in the POI form

In addition to that we have entry points for bundling for each :ref:`template module <template-modules>`. Those are based on the `index.ts` files inside the integreat_cms/static/js/template/ folder.
The templates with their own feature module are:

1. :github-source:`integreat_cms/cms/templates/settings/mfa/add_key.html`
2. :github-source:`integreat_cms/cms/templates/content_versions.html`
3. :github-source:`integreat_cms/cms/templates/dashboard/dashboard.html`
4. :github-source:`integreat_cms/cms/templates/events/event_form.html`
5. :github-source:`integreat_cms/cms/templates/languages/language_form.html`
6. :github-source:`integreat_cms/cms/templates/languagetreenodes/languagetreenode_form.html`
7. :github-source:`integreat_cms/cms/templates/pages/page_form.html`
8. :github-source:`integreat_cms/cms/templates/pages/page_xliff_import_view.html`
9. :github-source:`integreat_cms/cms/templates/pages/pages_page_tree.html`
10. :github-source:`integreat_cms/cms/templates/pois/poi_form.html`
11. :github-source:`integreat_cms/cms/templates/poicategories/poicategory_list.html`
12. :github-source:`integreat_cms/cms/templates/push_notifications/push_notification_form.html`
13. :github-source:`integreat_cms/cms/templates/regions/region_form.html`
14. :github-source:`integreat_cms/cms/templates/analytics/translation_coverage.html`
15. :github-source:`integreat_cms/cms/templates/translations/translations_management.html`

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

To create a feature module, a TypeScript file inside the folder ``/integreat_cms/static/js/feature/`` needs to be created. It should contain:

1. ``export const moduleName = <name-of-feature>``  
   (For convention's sake, we suggest using the filename in kebab-case)
2. ``const init = (root: HTMLElement) => { ... }``  
   (Inside this init function, the event listeners will be attached to the root element and/or its children)
3. ``export default init``

During the ``npm run build`` (which is executed during ``tools/run.sh``), a file ``registry.ts`` is updated with the new module.  
This registry is then used to dynamically import the module whenever the corresponding attribute is present in the DOM.

.. _template-modules:

Template modules
================

Template modules are TypeScript files that apply to only **one full-page template**.  

To create a new template module for a full-page template that does not yet use a template module, follow these steps:

1. Create a sub-folder inside the folder ``/integreat_cms/static/js/template/``.  
   The sub-folder's name should match the name of the full-page template it relates to.
2. Inside the folder, create a file ``index.ts``.  
   (You can add more files, which should be imported into ``index.ts``)
3. Add an entry point for the ``index.ts`` file inside ``webpack.config.js``.
4. Inside the template:
    - Add ``{% load render_bundle from webpack_loader %}`` to the top of the template if it is not there yet.
    - Add a block for JavaScript if not present:

      .. code-block:: html

          {% block javascript %}{% endblock javascript %}

    - Inside the JavaScript block, add:

      .. code-block:: html

          {% render_bundle 'name-of-entry-point' 'js' %}

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
