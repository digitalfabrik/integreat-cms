import fs from "fs";
import path from "path";

const docsDir = "./docs/src/frontend_md";
const mainFile = "README.md";

const addOrphan = (file: fs.PathOrFileDescriptor) => {
    const content = fs.readFileSync(file, "utf-8");
    if (!content.startsWith("---\norphan: true\n---")) {
        fs.writeFileSync(file, `---\norphan: true\n---\n\n${content}`);
    }
};

const walkFiles = (dir: string) => {
    for (const fileName of fs.readdirSync(dir)) {
        const fullPath = path.join(dir, fileName);
        if (fs.statSync(fullPath).isDirectory()) {
            walkFiles(fullPath);
        } else if (fullPath.endsWith(".md") && fullPath !== path.join(docsDir, mainFile)) {
            addOrphan(fullPath);
        }
    }
};

walkFiles(docsDir);
