import path from "node:path";

import { includeIgnoreFile } from "@eslint/compat";
import js from "@eslint/js";
import { defineConfig } from "eslint/config";
import { configs, plugins } from "eslint-config-airbnb-extended";
import { rules as prettierConfigRules } from "eslint-config-prettier";
import prettierPlugin from "eslint-plugin-prettier";
import preact from "eslint-config-preact";
import typescriptParser from "@typescript-eslint/parser";
import preferArrow from "eslint-plugin-prefer-arrow";
import globals from "globals";

const gitignorePath = path.resolve(".", ".gitignore");

const jsConfig = defineConfig([
    {
        name: "js/config",
        ...js.configs.recommended,
    },
    plugins.stylistic,
    plugins.importX,
    ...configs.base.recommended,
]);

// strip plugin registration from preactConfig to avoid conflict with eslint-config-airbnb-extended
const preactConfig = defineConfig([...preact].map(({ plugins: _plugins, ...config }) => config));

const reactConfig = defineConfig([plugins.react, plugins.reactHooks, plugins.reactA11y, ...configs.react.recommended]);

const typescriptConfig = defineConfig([
    plugins.typescriptEslint,
    ...configs.base.typescript,
    ...configs.react.typescript,
]);

const prettierConfig = defineConfig([
    {
        name: "prettier/plugin/config",
        plugins: {
            prettier: prettierPlugin,
        },
    },
    {
        name: "prettier/config",
        rules: {
            ...prettierConfigRules,
            "prettier/prettier": "error",
        },
    },
]);

export default defineConfig([
    includeIgnoreFile(gitignorePath),
    {
        ignores: [
            "**/dist/",
            "**/htmlcov/**",
            "**/node_modules/",
            "*.config.js",
            "*.json",
            "*.lock",
            ".eslintrc.js",
            ".venv/",
            "build/",
            "docs/",
            "package.json",
            "package-lock.json",
            "vitest.config.mts",
        ],
    },
    {
        languageOptions: {
            parser: typescriptParser,
            parserOptions: {
                ecmaVersion: "latest",
                sourceType: "module",
                projectService: true,
                ecmaFeatures: {
                    jsx: true,
                },
            },
            globals: {
                ...globals.browser,
                ...globals.es6,
            },
        },
    },
    ...jsConfig,
    ...reactConfig,
    ...preactConfig,
    ...typescriptConfig,

    {
        settings: {
            "import-x/resolver": {
                node: {
                    paths: ["src"],
                    extensions: [".js", ".jsx", ".ts", ".d.ts", ".tsx"],
                },
                typescript: {
                    project: "./tsconfig.json",
                },
                alias: {
                    map: [["~", path.resolve("./src")]],
                    extensions: [".js", ".jsx", ".ts", ".d.ts", ".tsx"],
                },
            },
        },
    },

    {
        plugins: {
            "prefer-arrow": preferArrow,
        },
        rules: {
            "@stylistic/lines-between-class-members": "off",
            "import-x/no-cycle": "off",

            "function-paren-newline": "off",
            "jsx-a11y/label-has-associated-control": "off",
            "jsx-a11y/no-noninteractive-element-interactions": "off",
            "jsx-a11y/no-static-element-interactions": "off",
            "no-restricted-syntax": "off",
            "react/jsx-props-no-spreading": "off",
            "react/no-unknown-property": "off",

            "import-x/extensions": "off",
            "import-x/no-extraneous-dependencies": "off",
            "import-x/prefer-default-export": "off",
            "indent": "off",
            "lines-between-class-members": "off",
            "react/jsx-filename-extension": "off",
            "react/jsx-fragments": "off",
            "react/require-default-props": "off",

            "default-case": "off",
            "no-unused-vars": "off",
            "no-use-before-define": "off",

            "curly": ["error", "all"],
            "func-names": "error",
            "no-magic-numbers": [
                "error",
                {
                    ignore: [-1, 0, 1, 2, 100],
                    ignoreArrayIndexes: true,
                },
            ],
            "no-mixed-operators": "error",
            "no-plusplus": ["error", { allowForLoopAfterthoughts: true }],
            "prefer-destructuring": ["error", { array: false }],
            "prefer-arrow/prefer-arrow-functions": "error",
            "prefer-object-spread": "error",
            "prefer-template": "error",
            "react/function-component-definition": ["error", { namedComponents: "arrow-function" }],
            "react-hooks/exhaustive-deps": "error",
            "vars-on-top": "error",
            "no-console": ["error", { allow: ["debug", "warn", "error"] }],
        },
    },

    {
        files: ["**/js/feature/**/*.ts"],
        rules: {
            "no-restricted-syntax": [
                "error",
                {
                    selector:
                        "CallExpression[callee.object.name='document'][callee.property.name=/^(querySelector|querySelectorAll|getElementById|getElementsByClassName|getElementsByTagName|getElementsByName)$/]",
                    message:
                        "Feature modules must not query the document directly. Use the root element passed to your init function instead.",
                },
                {
                    selector: "ExportDefaultDeclaration:not(:has(CallExpression[callee.name='defineFeature']))",
                    message: "Feature module default exports must use defineFeature().",
                },
            ],
        },
    },

    {
        files: ["**/*.js"],
        languageOptions: {
            parserOptions: {
                ecmaVersion: 2020,
                sourceType: "module",
            },
            globals: {
                tinymce: "readonly",
            },
        },
        rules: {
            "global-require": "off",
            "no-empty": "off",
            "no-unused-vars": "off",
            "no-undef": "off",
            "import-x/no-unresolved": "off",
        },
    },

    {
        files: ["**/*.ts", "**/*.mts", "**/*.cts", "**/*.tsx"],
        rules: {
            "no-undef": "off",
            "@typescript-eslint/no-explicit-any": "off",
            "@typescript-eslint/explicit-module-boundary-types": "off",
            "@typescript-eslint/strict-boolean-expressions": "off",
            "@typescript-eslint/await-thenable": "error",
            "@typescript-eslint/ban-ts-comment": ["error", { "ts-ignore": "allow-with-description" }],
            "@typescript-eslint/consistent-type-definitions": ["error", "type"],
            "@typescript-eslint/no-empty-function": "error",
            "@typescript-eslint/no-unused-vars": [
                "error",
                {
                    argsIgnorePattern: "_(unused)?",
                    varsIgnorePattern: "_(unused)?",
                    ignoreRestSiblings: true,
                },
            ],
            "@typescript-eslint/no-use-before-define": "error",
            "@typescript-eslint/switch-exhaustiveness-check": "error",
            "@typescript-eslint/no-unnecessary-type-assertion": "off",
            "@typescript-eslint/no-shadow": "off",
            "@typescript-eslint/prefer-destructuring": "off",
            "@typescript-eslint/array-type": "off",
            "@typescript-eslint/consistent-indexed-object-style": "off",
            "@typescript-eslint/no-inferrable-types": "off",
            "@typescript-eslint/no-unnecessary-template-expression": "off",
            "@typescript-eslint/no-unnecessary-type-arguments": "off",
            "@typescript-eslint/naming-convention": "off",
        },
    },

    ...prettierConfig,
]);
