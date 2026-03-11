/**
 * this file contains function for autocompletion of the event form fields
 */

const autocompleteEndDate = (event: Event) => {
    const startDateInput = event.target as HTMLInputElement;
    const endDateInput = document.getElementById("id_end_date") as HTMLInputElement;
    if (endDateInput.value.length === 0) {
        endDateInput.value = startDateInput.value;
    }
};

const autocompleteEndTime = (event: Event) => {
    const startTimeInput = event.target as HTMLInputElement;
    const endTimeInput = document.getElementById("id_end_time") as HTMLInputElement;
    if (endTimeInput.value.length === 0) {
        endTimeInput.value = startTimeInput.value;
    }
};

window.addEventListener("load", () => {
    if (document.getElementById("id_start_date") && document.getElementById("id_start_time")) {
        document.getElementById("id_start_date").addEventListener("focusout", autocompleteEndDate);
        document.getElementById("id_start_time").addEventListener("focusout", autocompleteEndTime);
    }
});
