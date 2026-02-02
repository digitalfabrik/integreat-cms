/**
 *  Updates the endDate and endTime Input fields with the startDate/startTime value if not set yet
 *
 */

const autocompleteEndDate = (startDateInput: HTMLInputElement, endDateInput: HTMLInputElement) => {
    if (endDateInput.value.length === 0) {
        const input = endDateInput;
        input.value = startDateInput.value;
    }
};

const autocompleteEndTime = (startTimeInput: HTMLInputElement, endTimeInput: HTMLInputElement) => {
    if (endTimeInput.value.length === 0) {
        const input = endTimeInput;
        input.value = startTimeInput.value;
    }
};

window.addEventListener("load", () => {
    const startDateInput = document.querySelector("#id_start_date") as HTMLInputElement;
    const startTimeInput = document.querySelector("#id_start_time") as HTMLInputElement;
    const endDateInput = document.querySelector("#id_end_date") as HTMLInputElement;
    const endTimeInput = document.querySelector("#id_end_time") as HTMLInputElement;

    if (startDateInput && endDateInput) {
        startDateInput.addEventListener("focusout", () => autocompleteEndDate(startDateInput, endDateInput));
    }

    if (startTimeInput && endTimeInput) {
        startTimeInput.addEventListener("focusout", () => autocompleteEndTime(startTimeInput, endTimeInput));
    }
});
