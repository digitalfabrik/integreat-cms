# 3. Use databse triggers for the complex database constraint to guarantee slug uniqueness

Date: 2026-05-06

## Status

Accepted

## Context

Slugs on translation instances are assumed to be unique per language and region (but not 
per foreign object - e.g. page_translations of the same page, can have the same slug). This
needs to be especially guaranteed as it breaks the search in the App. It is not possible to use
simple uniqueness constraints: A unique constraint basically creates an Index (can be 
partial when used with condition). But we need the condition "where page_id differs 
from other page_id". Meaning we need to be comparing two rows, which is not doable neither 
in Django nor SQL.

# Possible Solutions

- Database Triggers (CHOSEN)
- Denormalization of the region column + database triggers
- ExclusionConstraint + Database Triggers

## Decision

We use a database trigger that runs on INSERT and UPDATE, to guarantee that it
is impossible to enter new translation objects with duplicate slugs for pages, places and events.

## Consequences

- As the triggers will run on every INSERT and UPDATE, this might impact performance
- Pre-existing duplicates will not be flagged by the constraint - we provide a asynchronous 
management command that fixes all slugs in the database
