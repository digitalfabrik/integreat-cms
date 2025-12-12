# Architecture Decision Records

This directory houses the ADRs for Integreat CMS.
These are written notes of decisions regarding the architecture of the project.

As this project introduces keeping ADRs after substantial development already happened,
this collection starts off incomplete and fragmented,
with hopes of slowly adding past decisions retroactively.
Some decisions and details won't be able to be reconstructed.

---

This document outlines how these records are organized and formatted.
Note that this is done for convenience, to quickly understand how to navigate them, and technically not binding.
A binding description for how to keep ADRs would belong in the Process Decision Records (PDR).


## Format

Each ADR is associated with an unique, consecutive ID and a short, descriptive title.
Besides the file extension, the file name shall consist of the zero-padded ID combined with the title,
all converted to `kebab-case`, with any group consecutive special (space or not ASCII alphanumeric) characters replaced by a single dash (`-`).

ADRs shall be written in markdown.
The top level headline shall consist of the ID followed by a dot, a space and the title.
The date of creation shall be specified immediately after according to ISO 8601 (`yyyy-mm-dd`).
Under the second level headline `Status` the current status shall be noted, e.g. `Accepted` or `Superceded by [4. Some alternate decision](0004-some-alternate-decision.md)`

The rest should outline the decision and consequences clearly, but in brevity to keep the document readable.
It should cover architecture decisions, but not implementation details.
It is not further detailed here as the exact format is expected to vary a lot during this initial period.


## Tools

The described format makes these records easy to create, read, modify and search for with traditional plain text tools (e.g. `ls`, `less`, `grep`).
It is also compatible with https://github.com/npryce/adr-tools, which may be used to manage these as well.
