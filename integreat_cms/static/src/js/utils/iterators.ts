/* eslint-disable prefer-arrow/prefer-arrow-functions */

/**
 * Replacement for Iterator.some()
 *
 * Can be removed when upgrading to es2025.
 *
 * See https://developer.mozilla.org/de/docs/Web/JavaScript/Reference/Global_Objects/Iterator/some
 */
export function some<T>(Iterable: IterableIterator<T>, predicate: (item: T) => boolean): boolean {
    for (const item of Iterable) {
        if (predicate(item)) {
            return true;
        }
    }
    return false;
}

/**
 * Replacement for Iterator.every()
 *
 * Can be removed when upgrading to es2025.
 *
 * See https://developer.mozilla.org/de/docs/Web/JavaScript/Reference/Global_Objects/Iterator/every
 */
export function every<T>(Iterable: IterableIterator<T>, predicate: (item: T) => boolean): boolean {
    for (const item of Iterable) {
        if (!predicate(item)) {
            return false;
        }
    }
    return true;
}
