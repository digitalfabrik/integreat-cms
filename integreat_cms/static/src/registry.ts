type Init = (el: HTMLElement) => void | Promise<void>;

/**
 *  This registry record is automatically generated and enables dynamic imports in index.ts
 * based on what modules are required in the DOM
 * 
 *  To generate the registry run the command 'npm run generate:registry'
 * 
 *  In order to register a module export a 
 *  - export const moduleName of type string
 *  - export default function <name> of type (el: HTMLElement) => void 
 * 
 * @module registry
 * 
 */

/**
 * 
 * the registry record which is used in the main index.ts to dynamically import the modules
 */
export const registry: Record<string, () => Promise<{ default: Init }>> = {
  "search-query": () => import(/* webpackChunkName: "search-query" */"./js/search-query" as any).then(mod => ({
      default: mod.default as unknown as Init
    }))
};
// IMPORTANT: This file is auto-generated (by ./tools/generateRegistry.ts): do NOT edit by hand
