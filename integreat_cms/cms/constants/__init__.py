"""
Constants are used whenever we store values in the database which are chosen from a very limited set.
Defining constants here adds an abstract layer on top of the actual values that are stored in the database.
This improves readability of the code, enables auto-completion of values and minimizes the risk of mistakes.
The actual values which are stored in the database are completely irrelevant, because neither the developer,
nor the end users gets to see them.
The developer only sees the defined constant, and the end user only sees the (translated) string representation
defined in a mapping which is called ``CHOICES`` for every submodule.
"""
