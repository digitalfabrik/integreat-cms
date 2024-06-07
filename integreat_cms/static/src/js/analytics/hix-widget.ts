import { getContent } from "../forms/tinymce-init";
import { getCsrfToken } from "../utils/csrf-token";

let initialContent: string = null;
let initialHixScore: number = null;

const calculateBackgroundColor = (score: number, setOutdated: boolean): string => {
    const hixThresholdGood = 15;
    const hixThresholdOk = 7;

    if (setOutdated) {
        return "rgb(16, 111, 254, 0.3)";
    } else if (score >= hixThresholdGood) {
        return "rgb(74, 222, 128)";
    } else if (score > hixThresholdOk) {
        return "rgb(250, 204, 21)";
    }
    return "rgb(239, 68, 68)";
};

/**
 * Display the HIX score in a bar graph
 */
const updateHixBar = (score: number, setOutdated: boolean) => {
    const hixScore: HTMLElement = document.getElementById("hix-value");
    hixScore.textContent = `HIX ${score}`;

    const hixMaxScore = 20;
    const backgroundColor = calculateBackgroundColor(score, setOutdated);

    const hixBarFill: HTMLElement = document.getElementById("hix-bar-fill");
    const style = `width:${(score / hixMaxScore) * 100}%;background-color:${backgroundColor};`;
    hixBarFill.setAttribute("style", style);
};

/**
 * Display a label depending on the current HIX state
 * States are "updated", "outdated", "no-content" and "error"
 */
const updateHixStateLabel = (state: string) => {
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

    // Hide HIX feedback when the HIX state is not up-to-date
    if (state !== "updated") {
        document.getElementById("hix-feedback").classList.add("hidden");
    } else {
        document.getElementById("hix-feedback").classList.remove("hidden");
    }

    // Hide the loading spinner
    document.getElementById("hix-loading")?.classList.add("hidden");
};

/**
 * Display the HIX feedback details
 */
const updateHixFeedback = (hixFeedback: string) => {
    const feedbackSections = document.querySelectorAll("[hix-feedback-category]");
    const feedbackJson = JSON.parse(hixFeedback);

    let feedbackCount = 0;

    feedbackSections.forEach((feedbackSection) => {
        const categoryName = feedbackSection.getAttribute("hix-feedback-category");
        const feedbackEntry = feedbackJson.find((item: { category: string }) => item.category === categoryName);
        const feedbackResult = feedbackEntry ? feedbackEntry.result : [];

        if (feedbackResult.length > 0) {
            const categoryCount = feedbackSection.querySelector("span");
            categoryCount.textContent = feedbackResult.length;
            feedbackSection.classList.remove("hidden");
            feedbackCount += 1;
        } else {
            feedbackSection.classList.add("hidden");
        }
    });

    const feedbackContainer = document.getElementById("hix-feedback");
    if (feedbackCount === 0) {
        feedbackContainer.classList.add("hidden");
    } else {
        feedbackContainer.classList.remove("hidden");
    }
};

/**
 * Request current HIX data
 * @returns HIX score and HIX feedback
 */
const getHixData = async (): Promise<[number?, string?]> => {
    const updateButton = document.getElementById("btn-update-hix-value");
    const sentContent = getContent().trim();

    const response = await fetch(updateButton.dataset.url, {
        method: "POST",
        headers: {
            "X-CSRFToken": getCsrfToken(),
        },
        body: JSON.stringify({
            text: sentContent,
        }),
    });

    const json = await response.json();

    if (json.error || json.score === null) {
        updateHixStateLabel("error");
        return [];
    } else {
        updateHixStateLabel("updated");
        initialContent = sentContent;
        return [json.score, JSON.stringify(json.feedback)];
    }
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
    const updateMTAvailability = (hixValue: number) => {
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

    const initHixWidget = async () => {
        initialContent = getContent().trim();

        if (!initialContent) {
            updateHixStateLabel("no-content");
            return;
        }

        const hixContainer = document.getElementById("hix-container");

        let hixScore = parseFloat(hixContainer.dataset.initialHixScore);
        let hixFeedback = hixContainer.dataset.initialHixFeedback;

        if (!hixScore) {
            const response = await getHixData();
            if (response != null) {
                hixScore = response[0];
                hixFeedback = response[1];
            }
        }

        if (hixScore != null) {
            initialHixScore = hixScore;
            updateHixStateLabel("updated");
            updateHixBar(initialHixScore, false);
            updateHixFeedback(hixFeedback);
            updateMTAvailability(initialHixScore);
        }
    };

    // Set listener, that checks, if tinyMCE content has changed to update the
    // HIX status
    document.querySelectorAll("[data-content-changed]").forEach((element) => {
        // make sure initHixWidget is called only after tinyMCE is initialized
        element.addEventListener("tinyMCEInitialized", initHixWidget);
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
            updateHixBar(initialHixScore, labelState === "outdated");
            return updateHixStateLabel(labelState);
        });
    });

    // Set listener for update button
    document.getElementById("btn-update-hix-value").addEventListener("click", async (event) => {
        document.getElementById("hix-loading")?.classList.remove("hidden");
        event.preventDefault();

        const response = await getHixData();
        const hixScore = response[0];
        const hixFeedback = response[1];

        if (hixScore != null) {
            initialHixScore = hixScore;
            updateHixBar(initialHixScore, false);
            updateHixFeedback(hixFeedback);
            updateMTAvailability(initialHixScore);
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
