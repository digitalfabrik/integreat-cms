import { defineConfig } from "vitest/config";

export default defineConfig({
    server: {
        watch: {
            ignored: "**/.venv/**",
        },
    },
    test: {
        exclude: [
            "**/node_modules/**",
            "**/dist/**",
            "**/cypress/**",
            "**/.{idea,git,cache,output,temp,direnv}/**",
            "**/{karma,rollup,webpack,vite,vitest,jest,ava,babel,nyc,cypress,tsup,build}.config.*",
        ],
    },
});
