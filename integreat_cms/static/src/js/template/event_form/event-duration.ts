/**
 *
 * used in:
 * _event_duration_tab.html > date_and_time_box.html > event_form.html
 */

const toggleTabColorAndBorder = (tabId: string, color: string) => {
    const targetTab = document.getElementById(tabId);

    if (color === "bg-white") {
        targetTab.children[0].classList.remove("bg-water-500");
        targetTab.children[0].classList.add(color);
        targetTab.children[0].children[0].children[0].classList.remove("border-b");
    } else {
        targetTab.children[0].classList.remove("bg-white");
        targetTab.children[0].classList.add(color);
        targetTab.children[0].children[0].children[0].classList.add("border-b");
    }
};

const showOneTimeEventTab = () => {
    document.getElementById("end-date").classList.add("hidden");
    document.getElementById("recurrence-setting").classList.remove("hidden");
    document.getElementById("one-time-recurring-explanation").classList.remove("hidden");
    document.getElementById("long-term-explanation").classList.add("hidden");
    document.getElementById("long-term-info").classList.add("hidden");

    toggleTabColorAndBorder("one-time-and-recurring-tab", "bg-white");
    toggleTabColorAndBorder("long-term-tab", "bg-water-500");

    (document.getElementById("id_is_long_term") as HTMLInputElement).checked = false;
};

const showLongTermEventTab = () => {
    document.getElementById("end-date").classList.remove("hidden");
    document.getElementById("recurrence-setting").classList.add("hidden");
    document.getElementById("one-time-recurring-explanation").classList.add("hidden");
    document.getElementById("long-term-explanation").classList.remove("hidden");
    document.getElementById("long-term-info").classList.remove("hidden");

    toggleTabColorAndBorder("one-time-and-recurring-tab", "bg-water-500");
    toggleTabColorAndBorder("long-term-tab", "bg-white");

    (document.getElementById("id_is_long_term") as HTMLInputElement).checked = true;
};

const alignTabHeight = () => {
    document.getElementById("long-term-text").style.height =
        `${document.getElementById("one-time-and-recurring-text").offsetHeight}px`;
};

window.addEventListener("load", () => {
    document.getElementById("one-time-and-recurring-tab")?.addEventListener("click", showOneTimeEventTab);
    document.getElementById("long-term-tab")?.addEventListener("click", showLongTermEventTab);

    document.querySelector("option[value=DAILY]")?.classList.add("hidden");

    if (document.getElementById("long-term-tab")) {
        alignTabHeight();
        window.addEventListener("resize", alignTabHeight);
    }
});
