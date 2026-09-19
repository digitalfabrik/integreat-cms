/* eslint-disable prefer-arrow/prefer-arrow-functions */

/**
 * Adds or removes a list of tokens to/from a DOMTokenList.
 */
export function domTokenListToggle(domTokenList: DOMTokenList, value: boolean, ...tokens: string[]) {
    if (value) {
        domTokenList.add(...tokens);
    } else {
        domTokenList.remove(...tokens);
    }
}
