/**
 * this file contains function for autocompletion of the event form fields
 */

window.addEventListener("load", () => {
    if (document.getElementById("id_start_date") && document.getElementById("id_start_time")) {
        document.getElementById("id_start_date").addEventListener("focusout", autocompleteEndDate);
        document.getElementById("id_start_time").addEventListener("focusout", autocompleteEndTime);
    }
});

function autocompleteEndDate(event: Event) {
    let startDateInput = event.target as HTMLInputElement;
    let endDateInput = document.getElementById("id_end_date") as HTMLInputElement;
    if (endDateInput.value.length === 0) {
        endDateInput.value = startDateInput.value;
    }
}

function autocompleteEndTime(event: Event) {
    let startTimeInput = event.target as HTMLInputElement;
    let endTimeInput = document.getElementById("id_end_time") as HTMLInputElement;
    if (endTimeInput.value.length === 0) {
        endTimeInput.value = startTimeInput.value;
    }
}
