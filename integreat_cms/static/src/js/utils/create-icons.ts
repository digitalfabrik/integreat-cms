import { createIcons, icons } from "lucide";

// This function renders all <i icon-name="..."> children of `root`
export const createIconsAt = (root: HTMLElement) => {
    createIcons({
        nameAttr: "icon-name",
        icons,
        attrs: { class: "inline-block" },
        root,
    });
};
