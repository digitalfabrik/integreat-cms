import { defineConfig } from "vitest/config";

export default defineConfig({
    server: {
        watch: {
            ignored: "**/.venv/**",
        },
    },
});
