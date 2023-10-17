/*
 * This component renders the input fields for opening hours of locations
 */
import { StateUpdater, useEffect, useState } from "preact/hooks";
import cn from "classnames";
import { XCircle, CalendarClock } from "lucide-preact";

import { deepCopy } from "../../../utils/deep-copy";
import { OpeningHours } from "../index";

type Props = {
    openingHoursState: [OpeningHours[], StateUpdater<OpeningHours[]>];
    selectedDaysState: [number[], StateUpdater<number[]>];
    translations: any;
    days: any;
};

const OpeningHoursInputFields = ({ openingHoursState, selectedDaysState, translations, days }: Props) => {
    // This state contains the current opening hours
    const [openingHours, setOpeningHours] = openingHoursState;
    // This state contains the days which are currently selected for being edited
    const [selectedDays, setSelectedDays] = selectedDaysState;
    // This state contains a buffer for all changes which are not yet saved
    const [openingHoursBuffer, setOpeningHoursBuffer] = useState<OpeningHours>(null);

    // Select or de-select a given day
    const toggleDay = (day: number) => {
        console.debug("Toggling day:", day);
        // Check whether day was already selected
        const index = selectedDays.indexOf(day);
        const newSelectedDay = selectedDays.slice();
        if (index === -1) {
            // If not, add to the array
            newSelectedDay.push(day);
            setSelectedDays(newSelectedDay);
        } else if (selectedDays.length > 1) {
            // Else, remove it (if there is at least one day remaining)
            newSelectedDay.splice(index, 1);
            setSelectedDays(newSelectedDay);
        }
    };

    // Reset to one empty time slot
    const resetTimeSlots = (element: OpeningHours) => {
        /* eslint-disable-next-line no-param-reassign */
        element.timeSlots = [{ start: "", end: "" }];
    };

    // Add a new time slot input fields
    const addTimeSlot = () => {
        console.debug("Adding time slot");
        // Create new object instead of reference to existing one
        const newOpeningHoursBuffer = deepCopy(openingHoursBuffer);
        newOpeningHoursBuffer.timeSlots.push({
            start: "",
            end: "",
        });
        setOpeningHoursBuffer(newOpeningHoursBuffer);
    };

    // Remove the given time slot
    const removeTimeSlot = (event: Event, index: number) => {
        event.preventDefault();
        console.debug("Removing time slot:", index);
        // Create new object instead of reference to existing one
        const newOpeningHoursBuffer = deepCopy(openingHoursBuffer);
        // If only one slot is left, clear its values instead of removing
        if (openingHoursBuffer.timeSlots.length === 1) {
            resetTimeSlots(newOpeningHoursBuffer);
        } else {
            newOpeningHoursBuffer.timeSlots.splice(index, 1);
        }
        setOpeningHoursBuffer(newOpeningHoursBuffer);
    };

    // When the closed checkbox is changed, write the changes to the buffer
    const updateClosed = ({ target }: Event) => {
        console.debug("Changed closed checkbox:", target);
        // Create new object instead of reference to existing one
        const newOpeningHoursBuffer = deepCopy(openingHoursBuffer);
        newOpeningHoursBuffer.closed = (target as HTMLInputElement).checked;
        // If closed was checked, disable all day
        if (newOpeningHoursBuffer.closed) {
            newOpeningHoursBuffer.allDay = false;
            resetTimeSlots(newOpeningHoursBuffer);
        }
        setOpeningHoursBuffer(newOpeningHoursBuffer);
    };

    // When the all day checkbox is changed, write the changes to the buffer
    const updateOpenAllDay = ({ target }: Event) => {
        console.debug("Changed all day checkbox:", target);
        // Create new object instead of reference to existing one
        const newOpeningHoursBuffer = deepCopy(openingHoursBuffer);
        newOpeningHoursBuffer.allDay = (target as HTMLInputElement).checked;
        // If all day was checked, disable closed
        if (newOpeningHoursBuffer.allDay) {
            newOpeningHoursBuffer.closed = false;
            resetTimeSlots(newOpeningHoursBuffer);
        }
        setOpeningHoursBuffer(newOpeningHoursBuffer);
    };

    // When the appointment only checkbox is changed, write the changes to the buffer
    const updateAppointmentOnly = ({ target }: Event) => {
        console.debug("Changed appointment only checkbox:", target);
        // Create new object instead of reference to existing one
        const newOpeningHoursBuffer = deepCopy(openingHoursBuffer);
        newOpeningHoursBuffer.appointmentOnly = (target as HTMLInputElement).checked;
        setOpeningHoursBuffer(newOpeningHoursBuffer);
    };

    // When the opening time is updated, write the changes to the buffer
    const updateOpeningTime = ({ target }: Event) => {
        const timeInput = target as HTMLInputElement;
        console.debug("Changed opening time to:", timeInput.value);

        // Remove red border in case there was an error before
        document.getElementById(`time_slot_error_${timeInput.dataset.index}`).classList.add("hidden");
        timeInput.classList.remove("border-red-500");

        // Create new object instead of reference to existing one
        const newOpeningHoursBuffer = deepCopy(openingHoursBuffer);
        // If a valid value was entered, assume that both all day and closed are false
        if (timeInput.value !== "") {
            newOpeningHoursBuffer.allDay = false;
            newOpeningHoursBuffer.closed = false;
        }
        const index = parseInt(timeInput.dataset.index, 10);
        newOpeningHoursBuffer.timeSlots[index] = { ...newOpeningHoursBuffer.timeSlots[index], start: timeInput.value };
        setOpeningHoursBuffer(newOpeningHoursBuffer);
    };

    // When the closing time is updated, write the changes to the buffer
    const updateClosingTime = ({ target }: Event) => {
        const timeInput = target as HTMLInputElement;
        console.debug("Changed closing time to:", timeInput.value);

        // Remove red border in case there was an error before
        document.getElementById(`time_slot_error_${timeInput.dataset.index}`).classList.add("hidden");
        timeInput.classList.remove("border-red-500");

        // Create new object instead of reference to existing one
        const newOpeningHoursBuffer = deepCopy(openingHoursBuffer);
        // If a valid value was entered, assume that both all day and closed are false
        if (timeInput.value !== "") {
            newOpeningHoursBuffer.allDay = false;
            newOpeningHoursBuffer.closed = false;
        }
        const index = parseInt(timeInput.dataset.index, 10);
        newOpeningHoursBuffer.timeSlots[index] = { ...newOpeningHoursBuffer.timeSlots[index], end: timeInput.value };
        setOpeningHoursBuffer(newOpeningHoursBuffer);
    };

    // Close the input field widget by selecting no days
    const closeInputFields = (event?: Event) => {
        event?.preventDefault();
        console.debug("Closing input widget", openingHours);
        setSelectedDays([]);
        setOpeningHoursBuffer(null);
    };

    const save = (event: Event) => {
        event.preventDefault();
        console.debug("Save current buffer");
        // Validate time inputs
        let errorsOccurred = false;
        let lastTimeSlotEmpty = false;
        openingHoursBuffer.timeSlots.forEach((timeSlot, index) => {
            const timeSlotError = document.getElementById(`time_slot_error_${index}`);
            const openingTimeInput = document.getElementById(`opening_time_${index}`);
            const closingTimeInput = document.getElementById(`closing_time_${index}`);
            if (!timeSlot.start && !timeSlot.end) {
                // Only allow the last time slot to be empty when it's either open all day or closed or there are other slots
                if (index !== openingHoursBuffer.timeSlots.length - 1) {
                    // Require all slots except the last one
                    console.error("Error occurred: Only the last time slot can be empty");
                    openingTimeInput.classList.add("border-red-500");
                    closingTimeInput.classList.add("border-red-500");
                    timeSlotError.textContent = translations.errorOnlyLastSlotEmpty;
                } else if (index === 0 && !openingHoursBuffer.closed && !openingHoursBuffer.allDay) {
                    // Require the last slot when the location is not closed and not open all day and there are no other slots
                    console.error("Either closed, or all day, or one time slot is required.");
                    openingTimeInput.classList.add("border-red-500");
                    closingTimeInput.classList.add("border-red-500");
                    timeSlotError.textContent = translations.errorLastSlotRequired;
                } else {
                    // If the last slot is empty (but allowed to), save it for later so it can be removed
                    lastTimeSlotEmpty = true;
                    return;
                }
            } else if (!timeSlot.start) {
                console.error("Error occurred: opening time is missing");
                openingTimeInput.classList.add("border-red-500");
                timeSlotError.textContent = translations.errorOpeningTimeMissing;
            } else if (!timeSlot.end) {
                console.error("Error occurred: closing time is missing:", timeSlot.start);
                closingTimeInput.classList.add("border-red-500");
                timeSlotError.textContent = translations.errorClosingTimeMissing;
            } else if (timeSlot.start > timeSlot.end) {
                console.error("Error occurred: closing time earlier than opening time:", timeSlot.start);
                closingTimeInput.classList.add("border-red-500");
                timeSlotError.textContent = translations.errorClosingTimeEarlier;
            } else if (timeSlot.start === timeSlot.end) {
                console.error("Error occurred: closing time identical with opening time:", timeSlot.start);
                closingTimeInput.classList.add("border-red-500");
                timeSlotError.textContent = translations.errorClosingTimeIdentical;
            } else if (index > 0 && timeSlot.start < openingHoursBuffer.timeSlots[index - 1].end) {
                console.error(
                    "Error occurred: Opening time is earlier than the closing time of the previous time slot"
                );
                openingTimeInput.classList.add("border-red-500");
                timeSlotError.textContent = translations.errorOpeningTimeEarlier;
            } else if (index > 0 && timeSlot.start === openingHoursBuffer.timeSlots[index - 1].end) {
                console.error(
                    "Error occurred: Opening time is identical with the closing time of the previous time slot"
                );
                openingTimeInput.classList.add("border-red-500");
                timeSlotError.textContent = translations.errorOpeningTimeIdentical;
            } else {
                // Everything looks good - don't show the error
                return;
            }
            // Show error
            timeSlotError.classList.remove("hidden");
            errorsOccurred = true;
        });
        // If error occurred, do not proceed with saving
        if (errorsOccurred) {
            return;
        }
        // If the last time slot is empty, remove it
        if (lastTimeSlotEmpty) {
            openingHoursBuffer.timeSlots.pop();
        }
        // Create shallow clone of opening hours
        const newOpeningHours = openingHours.slice();
        // For each selected day, set the opening hours to the current buffer
        selectedDays.forEach((day) => {
            // Create new object instead of reference to existing one
            newOpeningHours[day] = deepCopy(openingHoursBuffer);
        });
        // Save opening hours
        setOpeningHours(newOpeningHours);
        // Close input field
        closeInputFields();
    };

    // Initialize the buffer with the opening hours of the first day
    useEffect(() => {
        console.debug("Selected days updated:", selectedDays);
        if (openingHoursBuffer === null && selectedDays.length > 0) {
            // Create new object instead of reference to existing one
            const newOpeningHoursBuffer = deepCopy(openingHours[selectedDays[0]]);
            if (newOpeningHoursBuffer.timeSlots.length === 0) {
                resetTimeSlots(newOpeningHoursBuffer);
            }
            setOpeningHoursBuffer(newOpeningHoursBuffer);
            console.debug("Initialized opening hour buffer:", newOpeningHoursBuffer);
        }
    }, [selectedDays, openingHours, openingHoursBuffer]);

    return (
        <div>
            {openingHoursBuffer !== null && (
                <div>
                    <div
                        class="fixed inset-0 opacity-75 bg-gray-800 z-[100]"
                        onClick={closeInputFields}
                        onKeyDown={closeInputFields}
                    />
                    <div class="flex flex-col justify-center w-160 fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 z-[101]">
                        <div class="w-full rounded shadow-2xl bg-white">
                            <div class="flex justify-between font-bold rounded p-4 bg-water-500">
                                <div>
                                    <CalendarClock class="inline-block" />
                                    <span class="uppercase pl-2">{translations.openingHoursLabel}</span>
                                </div>
                                <button
                                    className="rounded-full hover:bg-blue-500 hover:text-white"
                                    onClick={closeInputFields}
                                    type="button">
                                    <XCircle className="inline-block" />
                                </button>
                            </div>
                            <div class="p-4 max-h-[calc(90vh-3.5rem)] overflow-y-auto">
                                <div class="flex flex-wrap justify-between">
                                    <p class="pb-4 w-full">{translations.selectText}</p>
                                    {days.all.map((day: number) => (
                                        <div
                                            key={day}
                                            className={cn(
                                                "rounded-full h-20 w-20 flex flex-wrap place-content-center hover:bg-blue-300 cursor-pointer",
                                                {
                                                    "bg-blue-400": selectedDays.indexOf(day) !== -1,
                                                },
                                                {
                                                    "bg-blue-100": selectedDays.indexOf(day) === -1,
                                                }
                                            )}
                                            onClick={() => toggleDay(day)}
                                            onKeyDown={() => toggleDay(day)}>
                                            <p>{translations.weekdays[day].slice(0, 2)}</p>
                                        </div>
                                    ))}
                                </div>
                                <div>
                                    <input
                                        type="checkbox"
                                        name="all_day"
                                        id="all_day"
                                        onChange={updateOpenAllDay}
                                        checked={openingHoursBuffer.allDay}
                                    />
                                    <label for="all_day" class="mt-4 mb-0">
                                        {translations.allDayLabel}
                                    </label>
                                </div>
                                <div>
                                    <input
                                        type="checkbox"
                                        name="closed"
                                        id="closed"
                                        onChange={updateClosed}
                                        checked={openingHoursBuffer.closed}
                                    />
                                    <label for="closed">{translations.closedLabel}</label>
                                </div>
                                <div>
                                    <input
                                        type="checkbox"
                                        name="appointment_only"
                                        id="appointment_only"
                                        onChange={updateAppointmentOnly}
                                        checked={openingHoursBuffer.appointmentOnly}
                                    />
                                    <label for="appointment_only" class="mt-0 mb-4">
                                        {translations.appointmentOnlyLabel}
                                    </label>
                                </div>
                                {openingHoursBuffer.timeSlots.map((timeSlot, index) => (
                                    <div
                                        // Force re-rendering of fields when a time slot is added or removed
                                        /* eslint-disable-next-line react/no-array-index-key */
                                        key={index + openingHoursBuffer.timeSlots.length}
                                        class="flex flex-wrap gap-4 pb-2">
                                        <fieldset class="border border-solid border-gray-500 p-2 grow">
                                            <legend class="text-sm">
                                                <label for={`opening_time_${index}`} class="my-0">
                                                    {translations.openingTimeLabel}
                                                </label>
                                            </legend>
                                            <input
                                                type="time"
                                                name={`opening_time_${index}`}
                                                id={`opening_time_${index}`}
                                                onInput={updateOpeningTime}
                                                value={timeSlot.start}
                                                data-index={index}
                                            />
                                        </fieldset>
                                        <fieldset class="border border-solid border-gray-500 p-2 grow">
                                            <legend class="text-sm">
                                                <label for={`closing_time_${index}`} class="my-0">
                                                    {translations.closingTimeLabel}
                                                </label>
                                            </legend>
                                            <input
                                                type="time"
                                                name={`closing_time_${index}`}
                                                id={`closing_time_${index}`}
                                                onInput={updateClosingTime}
                                                value={timeSlot.end}
                                                data-index={index}
                                            />
                                        </fieldset>
                                        <div class="flex items-center">
                                            <button
                                                className="rounded-full hover:text-red-500"
                                                title={translations.removeTimeSlotText}
                                                onClick={(event) => removeTimeSlot(event, index)}
                                                type="submit">
                                                <XCircle className="inline-block" />
                                            </button>
                                        </div>
                                        <div
                                            id={`time_slot_error_${index}`}
                                            className="w-full bg-red-100 border-l-4 border-red-500 text-red-500 px-4 py-3 hidden"
                                            role="alert"
                                        />
                                    </div>
                                ))}
                                <button class="block" onClick={addTimeSlot} onKeyDown={addTimeSlot} type="button">
                                    {translations.addMoreText}
                                </button>
                                <div class="flex flex-wrap justify-end gap-4">
                                    <button class="btn btn-outline" onClick={closeInputFields} type="button">
                                        {translations.cancelText}
                                    </button>
                                    <button class="btn" onClick={save} type="button">
                                        {translations.saveText}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};
export default OpeningHoursInputFields;
