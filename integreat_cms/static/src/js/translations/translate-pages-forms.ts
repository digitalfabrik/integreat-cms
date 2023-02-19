import { getElement } from "dropzone";

/**
 * Eventlistener for all checkbox elements in every selectionbox of every page to translate
 * (translation/translate-pages)
 * select all, when 'all' is checked
 * change bg-color, when checked,
 * enable submit-button, if any language is selected
 */
window.addEventListener("load", () => {
    // event handler to toggle checkbox
    const selectLists = document.querySelectorAll('ul[id^="translate-language-selector-ul-"]');
    // loop over all ul-elements
    selectLists.forEach((selectList) => {
        const pageId = selectList.id.split("-").pop();
        const checkboxes = selectList.querySelectorAll('input[type="checkbox"]') as NodeListOf<HTMLInputElement>;
        const submitBtn = document.getElementById("translate-page-submit-" + pageId) as HTMLButtonElement;
        // loop over all input - checkboxes inside ul element
        checkboxes.forEach((checkbox) => {
            // event handler on change for each checkbox
            checkbox.addEventListener("change", function (event) {
                const targetCheckbox = event.target as HTMLInputElement; // change type to HTMLInputElement
                if (targetCheckbox.id == "select-all") {
                    changeAllCheckboxes(checkboxes, targetCheckbox);
                    toggleBgColor(checkboxes);
                }
                toggleBgColor(checkbox);
                if (submitBtn) {
                    toggleSubmitButtonWhenSelected(checkboxes, submitBtn);
                }
            });
        });
    });

    /**
     * toggles background-color when checkbox is checked
     *
     * @param checkboxes list of checkboxes if 'select all' is checked as NodeListOf<HTMLInputElement>, else single checkbox as HTMLInputElement
     * */
    function toggleBgColor(checkboxes: NodeListOf<HTMLInputElement> | HTMLInputElement) {
        const checkboxList = checkboxes instanceof NodeList ? Array.from(checkboxes) : [checkboxes];
        checkboxList.forEach((checkbox: HTMLInputElement) => {
            console.log(checkbox);
            if (checkbox.checked) {
                checkbox.parentElement.classList.remove("bg-white");
                checkbox.parentElement.classList.add("bg-gray-200");
            } else {
                checkbox.parentElement.classList.remove("bg-gray-200");
                checkbox.parentElement.classList.add("bg-white");
            }
        });
    }
});

/**
 * enables submit button, if any language is selected, disables if none
 *
 * @param checkboxes list of input elements as NodeListOf<HTMLInputElement>
 * @param submitbutton submit-button which should enabled/disabled as HTMLButtonElement
 */
function toggleSubmitButtonWhenSelected(checkboxes: NodeListOf<HTMLInputElement>, submitbutton: HTMLButtonElement) {
    let anyLanguageSelected = false;
    for (const checkbox of checkboxes) {
        if (checkbox.checked) {
            anyLanguageSelected = true;
            break;
        }
    }
    console.log(anyLanguageSelected);
    if (anyLanguageSelected) submitbutton.disabled = false;
    else submitbutton.disabled = true;
}

/**
 * toggle all checkboxes if 'select all' is checked to either all checked or all unchecked
 *
 * @param checkboxes all input elements in the selectlist as NodeListOf<HTMLInputElement>
 * @param selectAllCheckbox input element that works as select all switcher as HTMLInputElement
 */
function changeAllCheckboxes(checkboxes: NodeListOf<HTMLInputElement>, selectAllCheckbox: HTMLInputElement) {
    let checked = true;
    if (selectAllCheckbox.value == "all") {
        selectAllCheckbox.value = "none";
    } else if (selectAllCheckbox.value == "none") {
        checked = false;
        selectAllCheckbox.value = "all";
    }
    checkboxes.forEach((checkbox) => {
        const oC = checkbox as HTMLInputElement;
        oC.checked = checked;
    });
}
