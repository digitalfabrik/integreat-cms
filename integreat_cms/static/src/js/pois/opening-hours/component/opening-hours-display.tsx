/*
 * This component renders the opening hours of a location
 */
import { StateUpdater } from "preact/hooks";
import { OpeningHours } from "../index";

interface Props {
    openingHours: OpeningHours[];
    setSelectedDays: StateUpdater<number[]>;
    translations: any;
    days: any;
}

export default function OpeningHoursDisplay({ openingHours, setSelectedDays, translations, days }: Props) {
    // Select a given list of weekdays for the input fields
    const select = (event: Event, days: number[]) => {
        event.preventDefault();
        setSelectedDays(days);
    };

    return (
        <div>
            {openingHours.map((dayOpeningHours, day) => {
                return (
                    <div
                        title={translations.editWeekdayLabel}
                        className="flex flex-wrap justify-between gap-2 hover:bg-gray-50 p-4 border-b cursor-pointer"
                        onClick={() => setSelectedDays([day])}
                    >
                        <label class="secondary my-0 !cursor-pointer">{translations.weekdays[day]}</label>
                        <div class="text-right">
                            {dayOpeningHours.closed && translations.closedLabel}
                            {dayOpeningHours.allDay && translations.allDayLabel}
                            {dayOpeningHours.timeSlots.map((timeSlot) => {
                                return (
                                    <p>
                                        {timeSlot.start} - {timeSlot.end}
                                    </p>
                                );
                            })}
                        </div>
                    </div>
                );
            })}
            <div class="flex flex-wrap p-4 gap-2">
                <button class="btn btn-small !rounded-full" onClick={(event) => select(event, days.all)}>
                    {translations.editAllLabel}
                </button>
                <button class="btn btn-small !rounded-full" onClick={(event) => select(event, days.workingDays)}>
                    {translations.editWorkingDaysLabel}
                </button>
                <button class="btn btn-small !rounded-full" onClick={(event) => select(event, days.weekend)}>
                    {translations.editWeekendLabel}
                </button>
            </div>
        </div>
    );
}
