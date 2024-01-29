"""
Thile file contains the JSON schema for opening hours
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Final


JSON_SCHEMA: Final = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "array",
    "minItems": 7,
    "maxItems": 7,
    "items": {
        "type": "object",
        "properties": {
            "allDay": {"type": "boolean"},
            "closed": {"type": "boolean"},
            "appointmentOnly": {"type": "boolean"},
            "timeSlots": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "end": {
                            "type": "string",
                            "pattern": "^(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$",
                        },
                        "start": {
                            "type": "string",
                            "pattern": "^(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$",
                        },
                    },
                    "required": ["end", "start"],
                },
            },
        },
        "required": ["allDay", "closed", "appointmentOnly", "timeSlots"],
    },
}
