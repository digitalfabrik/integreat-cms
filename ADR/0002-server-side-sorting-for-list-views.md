# 2. Allow sorting in list views and handle sorting and pagination server-side

Date: 2026-01-28

## Status

Accepted

## Context

List views (for models such as Contacts, Events, Locations, ...) thus far did not
support sorting by parameters other than the default.
To develop a sort feature, a decision needed to be made whether the sorting should
be implemented server-side or client-side.
## Decision

Sorting will be handled server-side. This will allow an easy integration with Django's
built in pagination, which minimizes maintenance and avoids longer loading times.

## Consequences

As the sorting is handled by the server, a new request is sent every time a user
changes the sorting. However, this was deemed acceptable, since loading times
for list views should be fast enough to not negatively affect user experience.  
Client-side sorting and pagination would require to send a complete list of records,
which is less scalable and could drastically affect performance for large datasets.
