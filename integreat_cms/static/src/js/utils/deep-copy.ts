// Create a deep copy of an object without any references to existing ones
export function deepCopy(obj: any): any {
    return JSON.parse(JSON.stringify(obj));
}
