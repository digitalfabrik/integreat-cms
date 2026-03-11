window.addEventListener("load", () => {
    const table = document.getElementById("page_hix_list") as HTMLTableElement;
    const trigger = document.getElementById("toggle-hix-score-list-trigger");

    if (!table || !trigger) {
        return;
    }

    const maxRows = 10;
    if (table.tBodies[0].rows.length <= maxRows) {
        trigger.classList.add("hidden");
        return;
    }

    trigger.addEventListener("click", () => {
        table.classList.toggle("show-n-rows");
        [trigger.textContent, trigger.dataset.alternativeText] = [trigger.dataset.alternativeText, trigger.textContent];
    });
});
