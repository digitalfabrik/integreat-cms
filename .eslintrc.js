const path = require("path");

module.exports = {
    env: {
        es6: true,
        browser: true,
    },
    settings: {
        "import/resolver": {
            node: {
                paths: ["src"],
                extensions: [".js", ".jsx", ".ts", ".d.ts", ".tsx"],
            },
            typescript: {
                project: "./tsconfig.json",
            },
            alias: {
                map: [["~", path.resolve(__dirname, "./src")]],
                extensions: [".js", ".jsx", ".ts", ".d.ts", ".tsx"],
            },
        },
    },
    ignorePatterns: [
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
        "vitest.config.ts",
    ],

    extends: [
        "plugin:react/recommended",
        "plugin:jsx-a11y/recommended",
        "plugin:import/recommended",
        "plugin:import/typescript",
        "eslint-config-preact",
    ],
    parser: "@typescript-eslint/parser",
    parserOptions: {
        ecmaVersion: 6,
        sourceType: "module",
        EXPERIMENTAL_useProjectService: true,
        project: "./tsconfig.json",
        ecmaFeatures: {
            jsx: true,
        },
    },
    plugins: ["prefer-arrow", "prettier"],
    rules: {
        // probably a good idea to re-enable at some point
        "import/no-cycle": "off",

        // leave these to prettier
        "comma-dangle": "off",
        "implicit-arrow-linebreak": "off",
        "max-len": "off",
        "no-confusing-arrow": "off",
        "no-multiple-empty-lines": "off",
        "object-curly-newline": "off",
        "operator-linebreak": "off",
        "quote-props": "off",
        "react/jsx-closing-bracket-location": "off",
        "react/jsx-curly-newline": "off",
        "react/jsx-indent": "off",
        "react/jsx-indent-props": "off",
        "react/jsx-one-expression-per-line": "off",
        "wrap-iife": "off",

        // overly strict rules
        "function-paren-newline": "off",
        "jsx-a11y/label-has-associated-control": "off",
        "jsx-a11y/no-noninteractive-element-interactions": "off",
        "jsx-a11y/no-static-element-interactions": "off",
        "no-restricted-syntax": "off",
        "react/jsx-props-no-spreading": "off",
        "react/no-unknown-property": "off",

        // unwanted
        "import/extensions": "off",
        "import/no-extraneous-dependencies": "off",
        "import/prefer-default-export": "off",
        "indent": "off",
        "lines-between-class-members": "off",
        "react/jsx-filename-extension": "off",
        "react/jsx-fragments": "off",
        "react/require-default-props": "off",

        // better @typescript-eslint rules are available
        "default-case": "off", // => @typescript-eslint/switch-exhaustiveness-check
        "no-unused-vars": "off", // => @typescript-eslint/no-unused-vars
        "no-use-before-define": "off", // => @typescript-eslint/no-use-before-define

        // project-specific (general)
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

        // re-enabled from airbnb
        "import/first": ["error"],
        "import/order": [
            "error",
            {
                groups: [["builtin", "external", "internal"]],
                distinctGroup: true,
                sortTypesGroup: false,
                named: false,
                warnOnUnassignedImports: false,
            },
        ],
        "import/newline-after-import": ["error"],
        "camelcase": [
            "error",
            {
                properties: "never",
                ignoreDestructuring: false,
                ignoreImports: false,
                ignoreGlobals: false,
            },
        ],
        "no-nested-ternary": ["error"],
        "no-await-in-loop": ["error"],
        "consistent-return": ["error"],
        "dot-notation": [
            "error",
            {
                allowKeywords: true,
                allowPattern: "",
            },
        ],
        "eqeqeq": [
            "error",
            "always",
            {
                null: "ignore",
            },
        ],
        "guard-for-in": ["error"],
        "no-alert": ["warn"],
        "no-eval": ["error"],
        "no-implied-eval": ["error"],
        "no-loop-func": ["error"],
        "no-new-func": ["error"],
        "no-param-reassign": [
            "error",
            {
                props: true,
                ignorePropertyModificationsFor: [
                    "acc",
                    "accumulator",
                    "e",
                    "ctx",
                    "context",
                    "req",
                    "request",
                    "res",
                    "response",
                    "$scope",
                    "staticContext",
                ],
            },
        ],
        "no-return-assign": ["error", "always"],
        "no-self-compare": ["error"],
        "no-sequences": ["error"],
        "no-throw-literal": ["error"],

        "no-underscore-dangle": [
            "error",
            {
                allow: ["__REDUX_DEVTOOLS_EXTENSION_COMPOSE__"],
                allowAfterThis: false,
                allowAfterSuper: false,
                enforceInMethodNames: true,
                allowAfterThisConstructor: false,
                allowFunctionParams: true,
                enforceInClassFields: false,
                allowInArrayDestructuring: true,
                allowInObjectDestructuring: true,
            },
        ],
        "react/jsx-pascal-case": [
            "error",
            {
                allowAllCaps: true,
                ignore: [],
            },
        ],
        "react/no-array-index-key": ["error"],
        "react/button-has-type": [
            "error",
            {
                button: true,
                submit: true,
                reset: false,
            },
        ],
        "react/no-unstable-nested-components": ["error"],
        "react/no-invalid-html-attribute": ["error"],
        "import/no-named-as-default": ["error"],
        "arrow-body-style": [
            "error",
            "as-needed",
            {
                requireReturnForObjectLiteral: false,
            },
        ],
        "no-bitwise": ["error"],
        "no-continue": ["error"],
        "one-var": ["error", "never"],
        "spaced-comment": [
            "error",
            "always",
            {
                line: {
                    exceptions: ["-", "+"],
                    markers: ["=", "!", "/"],
                },
                block: {
                    exceptions: ["-", "+"],
                    markers: ["=", "!", ":", "::"],
                    balanced: true,
                },
            },
        ],
        "no-promise-executor-return": ["error"],
        "no-template-curly-in-string": ["error"],
        "no-unreachable-loop": [
            "error",
            {
                ignore: [],
            },
        ],
        "no-extend-native": ["error"],
        "no-lone-blocks": ["error"],
        "no-new": ["error"],
        "no-script-url": ["error"],
        "no-useless-return": ["error"],
        "no-void": ["error"],
        "yoda": ["error"],
    },
    overrides: [
        {
            files: ["*.js"],
            parser: "espree",
            parserOptions: {
                ecmaVersion: 2020,
                sourceType: "module",
            },
            extends: ["eslint:recommended"],
            plugins: [],
            rules: {
                "global-require": "off",
                "no-empty": "off",
                "no-unused-vars": "off",
                "no-undef": "off",
            },
            globals: {
                tinymce: "readonly",
            },
        },
        // officially recommended by TypeScript ESLint:
        // https://typescript-eslint.io/docs/linting/troubleshooting/
        {
            files: ["*.ts", "*.mts", "*.cts", "*.tsx"],
            extends: ["plugin:@typescript-eslint/recommended"],
            plugins: ["@typescript-eslint"],
            rules: {
                "no-undef": "off",
                "@typescript-eslint/no-explicit-any": "off",
                "@typescript-eslint/explicit-module-boundary-types": "off",
                "@typescript-eslint/strict-boolean-expressions": "off",
                // project-specific (typescript)
                "@typescript-eslint/await-thenable": "error",
                "@typescript-eslint/ban-ts-comment": "error",
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
                "@typescript-eslint/prefer-ts-expect-error": "error",
                "@typescript-eslint/switch-exhaustiveness-check": "error",
            },
        },
    ],
};
