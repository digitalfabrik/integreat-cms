from typing import Any


def get_default_opening_hours() -> list[dict[str, Any]]:
    """
    Return the default opening hours

    :return: The default opening hours
    """
    return [
        {"allDay": False, "closed": True, "appointmentOnly": False, "timeSlots": []}
        for _ in range(7)
    ]
