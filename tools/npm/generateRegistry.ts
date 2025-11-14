import fs from "fs";
import ts from "typescript";
import path from "path";
import prettier from "prettier";

const MODULES_DIR = path.resolve("./integreat_cms/static/src/js/feature");
const REGISTRY_DIR = path.resolve("./integreat_cms/static/src");
const REGISTRY_TS_FILE = path.join(REGISTRY_DIR, "registry.ts");

type ModuleEntry = {
    name: string;
    path: string;
};

const getRelativePath = (fullPath: string): string =>
    `./${path.relative(REGISTRY_DIR, fullPath).replace(/\\/g, "/").replace(/\.ts$/, "")}`;

/* eslint-disable no-console */
const logSkippedModule = (name: string, reasons: string[]) => {
    console.error(`Skipped feature module: ${name}`);
    console.group("Reasons:");
    reasons.forEach((reason) => console.error(`  - ${reason}`));
    console.groupEnd();
    console.info(
        "Tip: Make sure your module follows the pattern:\n" +
            "  1. export const moduleName = '<name-of-module>';\n" +
            "  2. const init = (root: HTMLElement) => { ... };\n" +
            "  3. export default init;\n" +
            "  4. Module placed under /feature folder\n" +
            "After fixing, run `npm run generate:registry` again."
    );
};

const initHasRootParameter = (initializer: ts.Expression | undefined): boolean => {
    if (!initializer) {
        return false;
    }
    if (ts.isArrowFunction(initializer) || ts.isFunctionExpression(initializer)) {
        const params = initializer.parameters;

        // Must have exactly one parameter
        if (params.length !== 1) {
            return false;
        }

        const param = params[0];

        // Parameter must be an identifier named "root"
        if (!ts.isIdentifier(param.name) || param.name.text !== "root") {
            return false;
        }

        // Parameter must have a type
        if (!param.type || !ts.isTypeReferenceNode(param.type)) {
            return false;
        }

        // Type must be HTMLElement
        const typeName = param.type.typeName;
        if (!ts.isIdentifier(typeName) || typeName.text !== "HTMLElement") {
            return false;
        }

        // All checks passed
        return true;
    }

    return false; // Not an arrow or function expression
};

const validateModule = (filePath: string) => {
    const content = fs.readFileSync(filePath, "utf-8");
    const sourceFile = ts.createSourceFile(filePath, content, ts.ScriptTarget.ESNext, true);

    let moduleName: string | null = null;
    let hasInit = false;
    let hasRootParam = false;
    let hasDefaultExport = false;

    ts.forEachChild(sourceFile, (node) => {
        // Check for `export const moduleName = '...'`
        if (ts.isVariableStatement(node) && node.modifiers?.some((m) => m.kind === ts.SyntaxKind.ExportKeyword)) {
            for (const decl of node.declarationList.declarations) {
                if (
                    ts.isIdentifier(decl.name) &&
                    decl.name.text === "moduleName" &&
                    decl.initializer &&
                    ts.isStringLiteral(decl.initializer)
                ) {
                    moduleName = decl.initializer.text;
                }
            }
        }

        // Check for `const init = (root: HTMLElement) => { ... }`
        if (ts.isVariableStatement(node)) {
            for (const decl of node.declarationList.declarations) {
                if (ts.isIdentifier(decl.name) && decl.name.text === "init") {
                    const initializer = decl.initializer;
                    hasInit = true;
                    hasRootParam = initHasRootParameter(initializer);
                }
            }
        }

        // Check for `export default init`
        if (ts.isExportAssignment(node) && ts.isIdentifier(node.expression) && node.expression.text === "init") {
            hasDefaultExport = true;
        }
    });

    const failureReasons: string[] = [];
    if (!moduleName) {
        failureReasons.push("moduleName not defined");
    } else if (!/^[a-z0-9-]+$/.test(moduleName)) {
        failureReasons.push("moduleName can only be lowercase and contain letters, numbers and '-'");
    }
    if (!hasInit) {
        failureReasons.push("init function not correctly defined");
    }
    if (!hasRootParam) {
        failureReasons.push("no root:HMTLElement defined");
    }
    if (!hasDefaultExport) {
        failureReasons.push("default init not correctly exported");
    }

    return { moduleName, failureReasons };
};

const getAllFiles = (
    dir: string,
    files: ModuleEntry[] = [],
    registeredModules: Set<string> = new Set()
): ModuleEntry[] => {
    const entries = fs.readdirSync(dir, { withFileTypes: true }).sort((a, b) => a.name.localeCompare(b.name));

    for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);
        if (entry.isDirectory()) {
            getAllFiles(fullPath, files, registeredModules);
        } else if (entry.name.endsWith(".ts")) {
            const { moduleName, failureReasons } = validateModule(fullPath);
            if (registeredModules.has(moduleName)) {
                failureReasons.push("a module with the same name has already been registered.");
            }
            if (failureReasons.length === 0) {
                const relativePath = getRelativePath(fullPath);
                files.push({ name: moduleName, path: relativePath });
                registeredModules.add(moduleName);
            } else {
                logSkippedModule(entry.name, failureReasons);
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
 *  To generate the registry run the command \`npm run generate:registry\`
 *
 *  In order to register a module, it must be located inside the \`/integreat_cms/static/src/js/feature/\` folder and it must contain:
 *  - \`export const moduleName = <name-of-module>;\`
 *  - \`const init = (root:HTMLElement) => {
 *          //register all eventListeners on or inside the root Element
 *      } \`
 *  - \`export default init;\`
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
    const files = getAllFiles(MODULES_DIR).sort((a, b) => a.name.localeCompare(b.name));

    const formatted = await prettier.format(generateRegistryTS(files), { parser: "typescript" });
    fs.writeFileSync(REGISTRY_TS_FILE, formatted, "utf-8");

    console.debug(` Generated registry at ${REGISTRY_TS_FILE} with ${files.length} modules.`);
};

main();
