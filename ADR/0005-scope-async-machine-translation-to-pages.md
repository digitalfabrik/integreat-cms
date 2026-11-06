# 5. Scope asynchronous machine translation to pages

Date: 2026-10-21

## Status

Accepted

## Context

Machine translation moved from synchronous processing to async Celery tasks (#4393). The backend supports all content types (pages, events, POIs and push notifications), but the frontend which shows the progress and the outcome of a translation only exists for pages so far.

Without this frontend, users get no feedback at all when translating other content types, translation reports for them are never consumed, and their translations are not protected against concurrent edits. For push notifications, "save and send" would even send the push notification before its translations are finished.

## Possible solutions

1. **Switch all content types at once** and add minimal feedback for the content types without a dedicated frontend.
2. **Switch content types one at a time**, each together with its frontend, and keep translating the others synchronously.

## Decision

Option 2: Only pages are translated asynchronously for now.

The content types which are translated asynchronously are listed in `integreat_cms.cms.constants.async_machine_translation.CONTENT_TYPES`. All other content types use the synchronous code path from before #4393.

Pages benefit the most from async translation, because bulk translations of many pages ran into request timeouts. A minimal frontend for the other content types would be thrown away once their dedicated frontend exists.

## Consequences

- The behavior of events, POIs and push notifications is unchanged, including the request timeouts for large bulk translations of events and POIs.
- Two code paths for machine translations exist until all content types are migrated.
- A content type is migrated by adding it to `CONTENT_TYPES` together with its frontend. Push notifications additionally need a send flow which waits for pending translations.
