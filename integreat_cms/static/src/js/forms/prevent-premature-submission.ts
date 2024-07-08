/**
 * We sometimes want to perform a background task when an input element looses focus.
 * If the focus loss is due to the user clicking on a submission button however, the
 * corresponding form will be submitted before the background task is initiated.
 * This class is a convenient wrapper for preventing this.
 *
 * See here for more: https://github.com/digitalfabrik/integreat-cms/pull/2636
 */
export default class SubmissionPrevention {
    watchedElements: HTMLElement[] = [];
    mostRecentlyClicked: HTMLElement = null;

    preventSubmission = (e: Event) => {
        e.preventDefault();
        this.mostRecentlyClicked = e.target as HTMLElement;
    };

    constructor(identifier: string) {
        const elements = document.querySelectorAll<HTMLElement>(identifier);
        elements.forEach((element) => {
            element.addEventListener("click", this.preventSubmission);
        });
        this.watchedElements = Array.from(elements);
    }

    release() {
        this.watchedElements.forEach((element) => {
            element.removeEventListener("click", this.preventSubmission);
        });
        if (this.mostRecentlyClicked !== null) {
            this.mostRecentlyClicked.click();
        }
    }
}
