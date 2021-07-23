declare module "*.svg" {
  const content: any;
  export default content;
}

declare module "htmldiff-js" {
  const InputMask: {
    execute: (a: string, b: string) => string
  };
  export default InputMask;
}
