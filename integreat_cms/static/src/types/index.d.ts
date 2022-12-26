declare module "*.svg" {
    const content: any;
    export default content;
}

declare module "htmldiff-js" {
    const InputMask: {
        execute: (a: string, b: string) => string;
    };
    export default InputMask;
}

type ReplaceElementOptions = {
    nameAttr: string;
    icons: { [key: string]: IconNode };
    attrs: Record<string, string>;
};

// Since the module does not export the replaceElement function, we have to declare it here
declare module "lucide/dist/esm/replaceElement" {
    const replaceElement: (element: Element, { nameAttr, icons, attrs }: ReplaceElementOptions) => void;
    export default replaceElement;
}
