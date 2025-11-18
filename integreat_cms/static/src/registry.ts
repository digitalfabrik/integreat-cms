/* eslint-disable */

/**
 *  This registry record is automatically generated and enables dynamic imports in index.ts
 * based on what modules are required in the DOM
 *
 *  To generate the registry run the command `npm run generate:registry`
 *
 *  In order to register a module, it must be located inside the `/integreat_cms/static/src/js/feature/` folder and it must contain:
 *  - `export const moduleName = <name-of-module>;`
 *  - `const init = (root:HTMLElement) => {
 *          //register all eventListeners on or inside the root Element
 *      } `
 *  - `export default init;`
 *
 * @module registry
 *
 */

type Init = (el: HTMLElement) => void | Promise<void>;

/**
 *
 * the registry record which is used in the main index.ts to dynamically import the modules
 */
export const registry: Record<string, () => Promise<{ default: Init }>> = {
  "search-query": () =>
    import(
      /* webpackChunkName: "search-query" */ "./js/feature/search-query" as any
    ).then((mod) => ({
      default: mod.default as unknown as Init,
    })),
};
// IMPORTANT: This file is auto-generated (by ./tools/npm/generateRegistry.ts): do NOT edit by hand
