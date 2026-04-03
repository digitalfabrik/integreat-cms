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

const mainPath = path.join(docsDir, mainFile);

const isOrphanCandidate = (fullPath: string) =>
    fs.statSync(fullPath).isFile() && fullPath.endsWith(".md") && fullPath !== mainPath;

const walkFiles = (fullPath: string) => {
    if (isOrphanCandidate(fullPath)) {
        addOrphan(fullPath);
    } else if (fs.statSync(fullPath).isDirectory()) {
        for (const fileName of fs.readdirSync(fullPath)) {
            walkFiles(path.join(fullPath, fileName));
        }
    }
};

walkFiles(docsDir);
