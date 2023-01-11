"""
This file contains the import config for XLIFF tests.
"""

#: The files to be uploaded and their expected response
XLIFF_IMPORTS = [
    (
        {
            "id": 1,
            "file": "augsburg_de_en_1_2_willkommen.xliff",
            "title": "Updated title",
            "content": "<p>Updated content</p>",
            "message": 'Page "Updated title" was imported successfully',
        },
        {
            "id": 2,
            "file": "augsburg_de_en_2_1_willkommen-in-augsburg.zip",
            "expected_file": "augsburg_de_en_2_1_willkommen-in-augsburg.xliff",
            "title": "Updated title",
            "content": "<p>Updated content</p>",
            "message": 'Page "Updated title" was imported successfully',
        },
    ),
    (
        {
            "id": 1,
            "file": "augsburg_de_en_1_2_willkommen_unchanged.xliff",
            "title": "Welcome",
            "content": "<p>Welcome to Augsburg</p>",
            "message": 'Page "Welcome" was imported without changes',
        },
        {
            "id": 5,
            "file": "augsburg_de_en_5_1_stadtplan_unchanged.xliff",
            "title": "City Map",
            "content": "<p>These changes were saved automatically</p>",
            "message": 'Page "City Map" was imported without changes',
        },
    ),
    (
        {
            "id": 1,
            "file": "augsburg_de_en_1_2_willkommen.xliff",
            "title": "Updated title",
            "content": "<p>Updated content</p>",
            "message": 'Page "Updated title" was imported successfully',
        },
        {
            "id": 1,
            "file": "augsburg_de_en_1_2_willkommen_conflict.xliff",
            "title": "Updated title",
            "content": "<p>Updated content</p>",
            "confirmation_message": (
                'Page <b>"Welcome"</b> from file <b>augsburg_de_en_1_2_willkommen.xliff</b> '
                "was also translated in file <b>augsburg_de_en_1_2_willkommen_conflict.xliff</b>. "
                "Please check which of the files contains the most recent version and upload only this file. "
                "If you confirm this import, only the first file will be imported and the latter will be ignored."
            ),
            "message": (
                'Page "Conflicting title" from the file <b>augsburg_de_en_1_2_willkommen_conflict.xliff</b> could not be imported. '
                "Check if you have uploaded any other conflicting files for this page."
            ),
        },
    ),
]
