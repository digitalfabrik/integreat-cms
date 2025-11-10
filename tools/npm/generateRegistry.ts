import fs from "fs";
import path from "path";

const MODULES_DIR = path.resolve("./integreat_cms/static/src");
const DOCS_DIR = path.resolve("./docs/src")
const REGISTRY_TS_FILE = path.join(MODULES_DIR, "registry.ts");

interface ModuleEntry {
    name: string;
    path: string;
}

function getAllFiles(dir: string, files: ModuleEntry[] = []): ModuleEntry[] {
    fs.readdirSync(dir, { withFileTypes: true }).forEach((entry) => {
        const fullPath = path.join(dir, entry.name);
        if (entry.isDirectory()) {
            getAllFiles(fullPath, files);
        } else if (entry.name.endsWith(".ts")) {
            const content = fs.readFileSync(fullPath, "utf-8");
            // a file only gets registered if the moduleName and the default function are exported
            const matchName = content.match(/export const moduleName\s*=\s*["'`](.+?)["'`]/) 
            const moduleName = matchName ? matchName[1] : null; 
            const matchDefault = content.match(/export default function/)
            if (moduleName && matchDefault) {
                const relativePath = getRelativePath(fullPath)
                files.push({ name: moduleName, path: relativePath })
            }
        }
    });
    return files;
}

function getRelativePath(path: string): string {
    return "./" +
        path
            .replace(/^.*?src[\\/]/, "")
            .replace(/\\/g, "/") //cleanup for windows
            .replace(/\.ts$/, ""); //dynamic imports do not take file-extension
}

function generateRegistryTS(registry: ModuleEntry[]): string {

    const mapping = registry
        .map(
            ({ name, path }) => {
                return `  "${name}": () => import(/* webpackChunkName: "${name}" */"${path}" as any).then(mod => ({
      default: mod.default as unknown as Init
    }))`;
            }
        )
        .join(",\n");

    return `type Init = (el: HTMLElement) => void | Promise<void>;

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
${mapping}
};
// IMPORTANT: This file is auto-generated (by ./tools/generateRegistry.ts): do NOT edit by hand
`;
}

function main() {
    const files = getAllFiles(MODULES_DIR);

    fs.writeFileSync(REGISTRY_TS_FILE, generateRegistryTS(files), "utf-8");

    console.log(` Generated registry at ${REGISTRY_TS_FILE} with ${files.length} modules.`);
}

main();