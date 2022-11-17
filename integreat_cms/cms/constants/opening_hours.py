"""
Thile file contains the JSON schema for opening hours
"""

JSON_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "array",
    "minItems": 7,
    "maxItems": 7,
    "items": {
        "type": "object",
        "properties": {
            "allDay": {"type": "boolean"},
            "closed": {"type": "boolean"},
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
        "required": ["allDay", "closed", "timeSlots"],
    },
}
