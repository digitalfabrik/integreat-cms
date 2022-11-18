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

interface Props {
    translations: any;
    days: any;
    initial: OpeningHours[];
}

interface TimeSlot {
    start: string;
    end: string;
}

export interface OpeningHours {
    timeSlots: TimeSlot[];
    allDay: boolean;
    closed: boolean;
}

export default function OpeningHoursWidget({ translations, days, initial }: Props) {
    // The state contains the current opening hours of the location
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

    return (
        <div>
            {openingHours && (
                <div className={"flex flex-col flex-grow min-w-0"}>
                    <textarea name="opening_hours" cols={40} rows={10} id="id_opening_hours" class="hidden">
                        {JSON.stringify(openingHours)}
                    </textarea>
                    <OpeningHoursDisplay
                        openingHours={openingHours}
                        setSelectedDays={setSelectedDays}
                        translations={translations}
                        days={days}
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
}

document.addEventListener("DOMContentLoaded", () => {
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
            />,
            el
        );
    });
});

(window as any).IntegreatOpeningHoursWidget = OpeningHoursWidget;
(window as any).preactRender = render;
(window as any).preactJSX = h;
