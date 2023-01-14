import { icons } from "lucide";
import replaceElement from "lucide/dist/esm/replaceElement";

// This function renders all <i icon-name="..."> children of `root`
export const createIconsAt = (root: HTMLElement) => {
    const elementsToReplace = root.querySelectorAll("[icon-name]");
    Array.from(elementsToReplace).forEach((element) =>
        replaceElement(element as HTMLElement, {
            nameAttr: "icon-name",
            icons,
            attrs: { class: "inline-block" },
        })
    );
};
