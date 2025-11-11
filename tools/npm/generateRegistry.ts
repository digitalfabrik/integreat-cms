import fs from "fs";
import path, { relative } from "path";
import prettier from "prettier";

const MODULES_DIR = path.resolve("./integreat_cms/static/src/js/feature");
const REGISTRY_DIR = path.resolve("./integreat_cms/static/src");
const REGISTRY_TS_FILE = path.join(REGISTRY_DIR, "registry.ts");

type ModuleEntry = {
    name: string;
    path: string;
};

const getRelativePath = (fullPath: string): string => {
    return (
        "./" +
        path
            .relative(REGISTRY_DIR, fullPath)
            .replace(/\\/g, "/")
            .replace(/\.ts$/, "")
    );
};

const getAllFiles = (dir: string, files: ModuleEntry[] = []): ModuleEntry[] => {
    const entries = fs
        .readdirSync(dir, { withFileTypes: true })
        .sort((a, b) => a.name.localeCompare(b.name));

    for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);
        if (entry.isDirectory()) {
            getAllFiles(fullPath, files);
        } else if (entry.name.endsWith(".ts")) {
            const content = fs.readFileSync(fullPath, "utf-8");
            // a file only gets registered if the moduleName and the default function are exported
            const matchName = content.match(/export const moduleName\s*=\s*["'`](.+?)["'`]/);
            const moduleName = matchName ? matchName[1] : null;
            const matchDefault = content.match(/export default init;/);
            const matchInit = content.match(
                /const init\s*=\s*\(\s*root\s*:\s*HTMLElement\s*\)\s*=>\s*{/
            );
            if (moduleName && matchDefault && matchInit) {
                const relativePath = getRelativePath(fullPath);
                files.push({ name: moduleName, path: relativePath });
            } else {
                console.error(`The file ${entry.name} could not be registered as a feature module. 
                    It needs to contain a 'export const moduleName = <name-of-module>.
                    And a 'export default init;', where init follows the pattern:
                    'const init = (root:HTMLElement) => {...}'
                    `)
            }
        }
    }
    return files;
};

const generateRegistryTS = (registry: ModuleEntry[]): string => {
    const mapping = registry
        .map(
            ({ name, path }) =>
                `    "${name}": () =>
        import(/* webpackChunkName: "${name}" */ "${path}" as any).then((mod) => ({
            default: mod.default as unknown as Init,
        })),`
        )
        .join("\n");

    return `/* eslint-disable */

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

type Init = (el: HTMLElement) => void | Promise<void>;

/**
 *
 * the registry record which is used in the main index.ts to dynamically import the modules
 */
export const registry: Record<string, () => Promise<{ default: Init }>> = {
${mapping}
};
// IMPORTANT: This file is auto-generated (by ./tools/npm/generateRegistry.ts): do NOT edit by hand
`;
};

const main = async () => {
    const files = getAllFiles(MODULES_DIR)
        .sort((a, b) => a.name.localeCompare(b.name));;

    const formatted = await prettier.format(generateRegistryTS(files), { parser: "typescript" })
    fs.writeFileSync(REGISTRY_TS_FILE, formatted, "utf-8");

    console.debug(` Generated registry at ${REGISTRY_TS_FILE} with ${files.length} modules.`);
};

main();
