/*
 * This component renders the opening hours of a location
 */
import cn from "classnames";
import { StateUpdater } from "preact/hooks";
import { OpeningHours } from "../index";

type Props = {
    openingHours: OpeningHours[];
    setSelectedDays: StateUpdater<number[]>;
    translations: any;
    days: any;
    canChangeLocation: boolean;
};

const OpeningHoursDisplay = ({ openingHours, setSelectedDays, translations, days, canChangeLocation }: Props) => {
    // Select a given list of weekdays for the input fields
    const select = (event: Event, days: number[]) => {
        event.preventDefault();
        setSelectedDays(days);
    };

    return (
        <div>
            {openingHours.map((dayOpeningHours, day) => (
                <div
                    key={translations.weekdays[day]}
                    title={translations.editWeekdayLabel}
                    className={cn("flex flex-wrap justify-between gap-2 p-4 border-b", {
                        "hover:bg-gray-50 cursor-pointer": canChangeLocation,
                    })}
                    onClick={() => canChangeLocation && setSelectedDays([day])}
                    onKeyDown={() => canChangeLocation && setSelectedDays([day])}>
                    <label class="secondary my-0 !cursor-pointer">{translations.weekdays[day]}</label>
                    <div class="text-right">
                        {dayOpeningHours.closed && translations.closedLabel}
                        {dayOpeningHours.allDay && translations.allDayLabel}
                        {dayOpeningHours.timeSlots.map((timeSlot) => (
                            <p key={`${timeSlot.start}-${timeSlot.end}`}>
                                {timeSlot.start} - {timeSlot.end}
                            </p>
                        ))}
                    </div>
                </div>
            ))}
            {canChangeLocation && (
                <div class="flex flex-wrap p-4 gap-2">
                    <button
                        class="btn btn-small !rounded-full"
                        onClick={(event) => select(event, days.all)}
                        type="button">
                        {translations.editAllLabel}
                    </button>
                    <button
                        class="btn btn-small !rounded-full"
                        onClick={(event) => select(event, days.workingDays)}
                        type="button">
                        {translations.editWorkingDaysLabel}
                    </button>
                    <button
                        class="btn btn-small !rounded-full"
                        onClick={(event) => select(event, days.weekend)}
                        type="button">
                        {translations.editWeekendLabel}
                    </button>
                </div>
            )}
        </div>
    );
};
export default OpeningHoursDisplay;
