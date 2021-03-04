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
declare module "tablesort" {
  class TableSort {
    constructor(node: HTMLElement);
  }
  export default TableSort;
}