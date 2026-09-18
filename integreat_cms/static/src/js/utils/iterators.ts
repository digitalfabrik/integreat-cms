/* eslint-disable prefer-arrow/prefer-arrow-functions */

/**
 * Replacement for Iterator.some()
 *
 * Can be removed when upgrading to es2025.
 *
 * See https://developer.mozilla.org/de/docs/Web/JavaScript/Reference/Global_Objects/Iterator/some
 */
export function some<T>(iterable: Iterable<T>, predicate: (item: T) => boolean): boolean {
    for (const item of iterable) {
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
export function every<T>(iterable: Iterable<T>, predicate: (item: T) => boolean): boolean {
    for (const item of iterable) {
        if (!predicate(item)) {
            return false;
        }
    }
    return true;
}

/**
 * Replacement for Iterator.filter()
 *
 * Can be removed when upgrading to es2025.
 *
 * See https://developer.mozilla.org/de/docs/Web/JavaScript/Reference/Global_Objects/Iterator/filter
 */
export function* filter<T>(
    iterator: Iterator<T>,
    predicate: (value: T, index: number) => boolean
): IterableIterator<T> {
    let index = 0;
    let step = iterator.next();

    while (!step.done) {
        // eslint-disable-next-line no-plusplus
        if (predicate(step.value, index++)) {
            yield step.value;
        }
        step = iterator.next();
    }
}
