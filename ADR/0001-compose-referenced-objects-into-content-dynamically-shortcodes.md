# 1. Compose referenced objects into content dynamically (Shortcodes)

Date: 2025-12-10

## Status

Accepted

## Context

We often reference objects like other pages, events, locations or contacts in content of page, event, location or imprint translations.
Historically, this has been done immediately when creating that translation,
with the consequence of not needing any additional processing when that content was requested,
but having to update that content whenever the referenced object was modified
and thus imposing the technical requirement to always know where content was being referenced in.

## Decision

We will switch to a dynamic approach, where the content only references the objects by an internal marker.
When the content is requested, any markers it contains will be replaced by the desired representation of the referenced object as it exists in the database at that time.

## Consequences

Content using such markers will always be up to date when delivered by our system.

When referenced content is changed, no extra action is needed anymore.
This should make such user actions in the CMS a bit quicker,
reduce the dependence on the link index kept by our `linkcheck` depencency and
reduce the number of content translation objects.

Every time content is requested we need additional processing time evaluating and replacing any markers.

This dynamic evaluation is additional complexity that lengthens the critical path to receiving content from essentially *get text from database → send to user* to *get text from database → parse text from database → run function to evaluate for each marker → concatenate resulting text → send to user*. If the evaluation function has a bug where it misbehaves when given some specific input, that will be very difficult to detect and fix.
