/*
 * This file contains the entrypoint for the opening hours preact component.
 *
 * Documentation of preact: https://preactjs.com/
 *
 */
import { render, h } from "preact";
import { useState, useEffect } from "preact/hooks";

import OpeningHoursDisplay from "./component/opening-hours-display";
import OpeningHoursInputFields from "./component/opening-hours-input-fields";

type Props = {
    translations: any;
    days: any;
    initial: OpeningHours[];
    canChangeLocation: boolean;
    updateDataRegisterCallback: (setter: (data: OpeningHours[]) => void) => void;
};

type TimeSlot = {
    start: string;
    end: string;
};

export type OpeningHours = {
    timeSlots: TimeSlot[];
    allDay: boolean;
    closed: boolean;
    appointmentOnly: boolean;
};

const OpeningHoursWidget = ({ translations, days, initial, canChangeLocation, updateDataRegisterCallback }: Props) => {
    // The state contains the current opening hours
    const [openingHours, setOpeningHours] = useState<OpeningHours[]>(initial);
    // This state contains the days which are currently selected for being edited
    const [selectedDays, setSelectedDays] = useState<number[]>([]);

    // Disable scrolling the body when the popup is visible
    useEffect(() => {
        const body = document.querySelector("body");
        if (selectedDays.length > 0) {
            body.classList.add("overflow-hidden");
        } else {
            body.classList.remove("overflow-hidden");
        }
    }, [selectedDays]);

    // This is a way to extract the new state from the preact component, so we can use it in our traditional, imperative spaghetti Typescript
    updateDataRegisterCallback(setOpeningHours);

    return (
        <div>
            {openingHours && (
                <div className="flex flex-col flex-grow min-w-0">
                    <textarea name="opening_hours" cols={40} rows={10} id="id_opening_hours" class="hidden">
                        {JSON.stringify(openingHours)}
                    </textarea>
                    <OpeningHoursDisplay
                        openingHours={openingHours}
                        setSelectedDays={setSelectedDays}
                        translations={translations}
                        days={days}
                        canChangeLocation={canChangeLocation}
                    />
                    {selectedDays.length > 0 && (
                        <OpeningHoursInputFields
                            openingHoursState={[openingHours, setOpeningHours]}
                            selectedDaysState={[selectedDays, setSelectedDays]}
                            translations={translations}
                            days={days}
                        />
                    )}
                </div>
            )}
        </div>
    );
};
export default OpeningHoursWidget;

// will be populated during initialization
let setOpeningHours: (_: OpeningHours[]) => void;

export const resetOpeningHoursListener = () => {
    const openingHourLocationData = JSON.parse(document.getElementById("openingHourLocationData").textContent);
    setOpeningHours(openingHourLocationData);
};

export const addOpeningHoursDataChangedListener = () => {
    const useLocationOpeningHours = document.getElementById("id_use_location_opening_hours") as HTMLInputElement;
    useLocationOpeningHours.checked = false;
};

export const addOpeningHoursListener = () => {
    document.querySelectorAll("opening-hours-widget").forEach((el) => {
        const openingHourConfigData = JSON.parse(document.getElementById("openingHourConfigData").textContent);
        const openingHourInitialData = JSON.parse(
            JSON.parse(document.getElementById("openingHourInitialData").textContent)
        );
        render(
            <OpeningHoursWidget
                {...openingHourConfigData}
                initial={openingHourInitialData}
                globalEdit={el.hasAttribute("data-enable-global-edit")}
                updateDataRegisterCallback={(setter: (data: OpeningHours[]) => void) => {
                    setOpeningHours = setter;
                }}
            />,
            el
        );
    });

    let updateLatch = 0;

    const useLocationOpeningHours: HTMLElement | null = document.getElementById(
        "id_use_location_opening_hours"
    ) as HTMLInputElement | null;
    if (useLocationOpeningHours) {
        useLocationOpeningHours.addEventListener("change", (e) => {
            // Only reset if we changed to adopt the opening hours from the location
            if ((e.target as HTMLInputElement).checked) {
                updateLatch += 1;
                const thisTimeAround = updateLatch;
                setTimeout(() => {
                    if (updateLatch === thisTimeAround) {
                        updateLatch = 0;
                    }
                }, 1);
                resetOpeningHoursListener();
            }
        });
    }

    const openingHoursTextarea = document.getElementById("id_opening_hours");
    if (openingHoursTextarea) {
        const observer = new MutationObserver((mutations) => {
            for (const mutation of mutations) {
                if (
                    mutation.type === "childList" ||
                    mutation.type === "attributes" ||
                    mutation.type === "characterData"
                ) {
                    if (updateLatch === 0) {
                        addOpeningHoursDataChangedListener();
                    }
                }
            }
        });

        observer.observe(document.getElementById("id_opening_hours"), {
            childList: true,
            characterData: true,
            subtree: true,
        });
    }
};

document.addEventListener("DOMContentLoaded", addOpeningHoursListener);

(window as any).IntegreatOpeningHoursWidget = OpeningHoursWidget;
(window as any).preactRender = render;
(window as any).preactJSX = h;
