// Create a deep copy of an object without any references to existing ones
export const deepCopy = (obj: any): any => JSON.parse(JSON.stringify(obj));
