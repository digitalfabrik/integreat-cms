import { getContent } from "../forms/tinymce-init";
import { getCsrfToken } from "../utils/csrf-token";

let initialContent: string = null;
let initialHixValue: number = null;

/* Display the HIX value using a bar chart */
const updateHixBar = (value: number, setOutdated: boolean) => {
    const roundedHixValue = Math.round(value * 100) / 100;

    const hixValue = document.getElementById("hix-value") as HTMLElement;
    hixValue.textContent = `HIX ${roundedHixValue}`;

    const hixMaxValue = 20;
    const hixThresholdGood = 15;
    const hixThresholdOk = 7;

    // Set color based on HIX value or use a separate color for outdated HIX
    let backgroundColor;
    if (setOutdated) {
        backgroundColor = "rgb(16, 111, 254, 0.3)";
    } else if (value > hixThresholdGood) {
        backgroundColor = "rgb(74, 222, 128)";
    } else if (value > hixThresholdOk) {
        backgroundColor = "rgb(250, 204, 21)";
    } else {
        backgroundColor = "rgb(239, 68, 68)";
    }

    const hixBarFill = document.getElementById("hix-bar-fill") as HTMLElement;
    const style = `width:${(roundedHixValue / hixMaxValue) * 100}%;background-color:${backgroundColor};`;
    hixBarFill.setAttribute("style", style);
};

/* Show a label based on a state defined in hix_widget.html.
 * States are "updated", "outdated", "no-content" and "error" */
const setHixLabelState = (state: string) => {
    document.querySelectorAll("[data-hix-state]").forEach((element) => {
        if (element.getAttribute("data-hix-state") === state) {
            element.classList.remove("hidden");
        } else {
            element.classList.add("hidden");
        }
    });

    // Hide the canvas if an error occurred
    if (state === "error" || state === "no-content") {
        document.getElementById("hix-container").classList.add("hidden");
    } else if (state === "updated") {
        document.getElementById("hix-container").classList.remove("hidden");
    }

    // Hide the button if there is no content or the value is up-to-date
    const updateButton = document.getElementById("btn-update-hix-value");
    if (state === "updated" || state === "no-content") {
        updateButton.classList.add("hidden");
    } else {
        updateButton.classList.remove("hidden");
    }

    // Hide the loading spinner
    document.getElementById("hix-loading")?.classList.add("hidden");
};

const getHixValue = async () => {
    const updateButton = document.getElementById("btn-update-hix-value");
    let result;
    const sentContent = getContent().trim();
    await fetch(updateButton.dataset.url, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCsrfToken(),
        },
        body: JSON.stringify({
            text: sentContent,
        }),
    })
        .then((response) => response.json())
        .then((json) => {
            const labelState = json.error || json.score === "undefined" ? "error" : "updated";
            setHixLabelState(labelState);
            result = json.score;
            if (!json.error) {
                initialContent = sentContent;
            }
        });
    return result;
};

window.addEventListener("load", async () => {
    // If the page has no diagram, do nothing
    if (!document.getElementById("hix-bar")) {
        return;
    }

    const toggleMTCheckboxes = (disabled: boolean) => {
        const checkboxes: NodeListOf<HTMLInputElement> = document.querySelectorAll(
            "#machine-translation-form input[type='checkbox']"
        );
        checkboxes.forEach((checkbox) => {
            const label = document.querySelector(`label[for='${checkbox.id}']`);
            if (disabled) {
                label.classList.add("pointer-events-none");
                checkbox.classList.add("fake-disable");
            } else {
                label.classList.remove("pointer-events-none");
                checkbox.classList.remove("fake-disable");
            }
        });
    };

    // Show or hide the checkboxes for automatic translation depending on the HIX score
    const toggleMTAvailability = (hixValue: number) => {
        const mtForm = document.getElementById("machine-translation-form");
        const hixScoreWarning = document.getElementById("hix-score-warning");
        const minimumHix = parseFloat(mtForm?.dataset.minimumHix);

        if (hixValue && hixValue < minimumHix) {
            hixScoreWarning?.classList.remove("hidden");
            toggleMTCheckboxes(true);
        } else {
            hixScoreWarning?.classList.add("hidden");
            toggleMTCheckboxes(false);
        }
    };

    const initHixValue = async () => {
        initialContent = getContent().trim();

        if (!initialContent) {
            setHixLabelState("no-content");
            return;
        }

        const hixValue =
            parseFloat(document.getElementById("hix-container").dataset.initialHixScore) || (await getHixValue());

        if (hixValue != null) {
            initialHixValue = hixValue;
            setHixLabelState("updated");
            updateHixBar(initialHixValue, false);
            toggleMTAvailability(initialHixValue);
        }
    };

    // Set listener, that checks, if tinyMCE content has changed to update the
    // HIX value status
    document.querySelectorAll("[data-content-changed]").forEach((element) => {
        // make sure initHixValue is called only after tinyMCE is initialized
        element.addEventListener("tinyMCEInitialized", initHixValue);
        element.addEventListener("contentChanged", () => {
            const content = getContent().trim();
            const labelState = (() => {
                if (!content) {
                    return "no-content";
                }
                if (content !== initialContent) {
                    return "outdated";
                }
                return "updated";
            })();
            updateHixBar(initialHixValue, labelState === "outdated");
            return setHixLabelState(labelState);
        });
    });

    // Set listener for update button
    document.getElementById("btn-update-hix-value").addEventListener("click", async (event) => {
        document.getElementById("hix-loading")?.classList.remove("hidden");
        event.preventDefault();

        const hixValue = await getHixValue();
        if (hixValue != null) {
            initialHixValue = hixValue;
            updateHixBar(initialHixValue, false);
            toggleMTAvailability(initialHixValue);
        }
    });

    const toggleHixIgnore = async () => {
        const hixIgnore = document.getElementById("id_hix_ignore") as HTMLInputElement;
        const hixBlock = document.getElementById("hix-block");
        const mtForm = document.getElementById("machine-translation-form");
        if (hixIgnore.checked) {
            hixBlock.classList.add("hidden");
            toggleMTCheckboxes(true);
            mtForm?.classList.add("hidden");
        } else {
            toggleMTCheckboxes(false);
            mtForm?.classList.remove("hidden");
            hixBlock.classList.remove("hidden");
        }
    };

    // Set listener to show/hide HIX widget when hix_ignore checkbox is clicked
    document.getElementById("id_hix_ignore")?.addEventListener("change", toggleHixIgnore);
    toggleHixIgnore();
});
