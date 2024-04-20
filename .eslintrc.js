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
    ],

    extends: [
        "airbnb",
        "airbnb/hooks",
        "eslint-config-preact",
        "plugin:@typescript-eslint/recommended",
        "plugin:import/typescript",
    ],
    parser: "@typescript-eslint/parser",
    parserOptions: {
        ecmaVersion: 6,
        sourceType: "module",
        project: "./tsconfig.json",
        ecmaFeatures: {
            jsx: true,
        },
    },
    plugins: ["@typescript-eslint", "prefer-arrow", "prettier"],
    rules: {
        // probably a good idea to re-enable at some point
        "@typescript-eslint/no-explicit-any": "off",
        "@typescript-eslint/explicit-module-boundary-types": "off",
        "import/no-cycle": "off",

        // leave these to prettier
        "comma-dangle": "off",
        "implicit-arrow-linebreak": "off",
        "max-len": "off",
        "no-confusing-arrow": "off",
        "no-console": "off",
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
        "@typescript-eslint/strict-boolean-expressions": "off",
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
    },
    overrides: [
        {
            files: ["*.js"],
            rules: {
                "global-require": "off",
            },
            globals: {
                tinymce: "readonly",
            },
        },
        // officially recommended by TypeScript ESLint:
        // https://typescript-eslint.io/docs/linting/troubleshooting/
        {
            files: ["*.ts", "*.mts", "*.cts", "*.tsx"],
            rules: {
                "no-undef": "off",
            },
        },
    ],
};
