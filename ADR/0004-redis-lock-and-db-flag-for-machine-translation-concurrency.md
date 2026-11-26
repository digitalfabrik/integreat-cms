# 4. Keep both a Redis lock and a DB flag for machine translation concurrency

Date: 2026-09-03

## Status

Accepted

## Context

Machine translation moved from synchronous processing to async Celery tasks (#4393). This requires answering, per `(content_type, object_id, language_slug)`: is a translation already running, and if so, which task? Two mechanisms ended up doing this:

- A Redis-backed lock (`cache.add()`/`cache.delete()`), keyed by `(content_type, object_id, language_slug)`, storing the Celery task ID as its value.
- A DB flag, `currently_in_machine_translation` on the translation row, checked as a fast path in `get_translation_state()` before falling back to the Redis lock.

Review raised a valid concern: having the same fact recorded in two places risks the two disagreeing, especially since Redis is not as durable as Postgres and should arguably be treated as a pure, disposable cache.

## Possible solutions

1. **Keep both.** Rely on a stale-state cleanup job (#4512) to catch and repair drift between them.
2. **Redis lock only.** Drop the DB flag.
3. **DB only.** Mirror the Redis lock's shape as a Postgres table (`content_type`, `object_id`, `language_slug`, `task_id`), drop the Redis lock entirely.

## Decision

Option 1: keep both.

The Redis lock does two things that are hard to replicate in the DB alone:

- **Atomic mutual exclusion, including for objects with no translation row yet.** `cache.add()` is atomic. A DB-based mutex needs `SELECT FOR UPDATE`, which requires a row to lock on — but a first-time translation has none. A placeholder row would introduce its own insert race and would pollute the translation model: every query against translations would need to filter placeholders out.
- **Per-language task ID storage.** A page can be translated into several languages simultaneously as independent tasks, so the lock must be scoped by language, not just by object. A DB-only equivalent (option 3) would essentially reimplement the same primitive as a Postgres table — same semantics, more latency, more moving parts, for no clear benefit over Redis.

The DB flag earns its place as a fast path (checked on rows already loaded, avoiding a Redis round trip for the common case). The Redis lock is the source of truth: the flag only mirrors it. The lock is always acquired before the flag is set and released before the flag is cleared, so a flag without a lock is stale by definition.

The flag was originally also meant as a safety net for scenarios where the Redis lock can be lost without the underlying task actually stopping. The concrete scenario that motivated this — `post_migrate` wiping the whole cache including in-flight locks — has since been fixed by removing `flush_cache_after_migrate` outright. With the cleanup job (#4512) treating the lock as authoritative, the flag no longer serves as such a safety net (see consequences).

## Consequences

- Two mechanisms record the same fact. If they disagree, a user could see a stuck "in progress" state or be able to queue a duplicate translation.
- Drift is repaired by the `cleanup_machine_translation_flags_and_reports` management command (#4512), which is run regularly and clears every flag whose lock does not exist anymore. Stale locks are not cleaned up actively: they expire via their TTL, after which the next run also clears the corresponding flags. So after a crashed worker, a translation can be shown as "in progress" for up to the lock TTL plus the cleanup interval.
- If the lock is lost while its task is still running (e.g. Redis eviction or restart, or the lock TTL expiring before a long-queued task finishes), the next cleanup run also clears the flag. The page then no longer shows as "in progress" and can be edited while the machine translation is still writing to it. This is accepted, since a lost lock already allows queueing a duplicate translation regardless of the flag.
- If drift turns out to be a recurring practical problem, the documented fallback is option 3 (DB-only, mirroring the Redis lock's shape in Postgres) — rejected here as premature, not as unworkable.
