# Diagnostic instrumentation

Read this when a failure spans components (CLI → build → deploy, request →
service → DB, test → fixture → app code) and Phase 2 evidence can't say
*where* good data turns bad — instrumentation replaces cross-layer guessing
with observation. It is scaffolding: it exists to kill hypotheses, and it
leaves no trace in the final diff.

## Contents
1. Where to instrument
2. Tag every probe
3. Log so the output answers the question
4. Heisenbugs — when observing changes the behavior
5. Cleanup is part of the fix

## 1. Where to instrument

Instrument **boundaries**, not everywhere: the seams where data crosses
from one component, layer, or process to another. One probe on each side
of every suspect boundary turns "somewhere in these three layers" into
"between B and C" in a single run — a binary search over the data path
instead of a re-read of all the code on it.

- Entry and exit of the suspect path: what came in, what went out.
- Both sides of serialization, IPC, network, and process boundaries —
  where representations change is where values silently change with them.
- Immediately **before** the operation that fails, not after — output that
  never prints because the crash came first is the most common way a probe
  lies to you. Log intent ("about to X with y=…"), then act.
- In tests, print to the mechanism that actually reaches you (often plain
  stderr) — a logger configured for the app may be captured, filtered, or
  silenced under the test runner, and a probe you can't see is evidence
  you don't have.

## 2. Tag every probe

Give every added probe a common, greppable marker, and when running
several hypotheses at once, a per-hypothesis tag:

```
console.error("[DEBUG H2] cache key at read:", key)   // H2: stale-key theory
```

- One tag per hypothesis lets a single run confirm/refute several theories
  at once, and keeps the mapping from output line → theory honest —
  untagged output from five probes degenerates into vibes.
- The common marker (`[DEBUG`) is what makes cleanup (§5) a grep instead
  of an archaeology dig.
- Keep probes on their own lines, never folded into existing statements —
  the probe must be removable without re-deriving what the line did
  before.

## 3. Log so the output answers the question

A probe earns its place by discriminating between hypotheses. For each
one, know what you expect to see if the hypothesis is true and if it is
false — a probe whose output you can't interpret either way is noise.

- Log **values and identities**, not narration: the actual key, length,
  type, pointer/id — "got here" only proves control flow, which is rarely
  the question.
- Include enough context to correlate across layers (request id, item
  index, timestamp) when the bug involves ordering or concurrency.
- Never log secrets or tokens — instrumentation output ends up in replies,
  CI logs, and shell history (the security rules apply to probes too).

## 4. Heisenbugs — when observing changes the behavior

Instrumentation is not free: probes add I/O and time, and for
timing-sensitive bugs (races, ordering, timeouts) that can shift the
schedule enough to hide the failure — the bug "disappears" under
observation and returns when probes are removed.

If adding probes makes an intermittent failure vanish: that *is* evidence —
you have a timing-dependent bug. Switch tactics rather than probing
harder: cheaper probes (append to an in-memory buffer, dump once at exit),
counters instead of per-event lines, or reproduce the race directly by
forcing the suspected interleaving (see the flaky-tests reference for the
usual causes). Don't conclude "fixed" because the instrumented run passes.

## 5. Cleanup is part of the fix

Before presenting the fix, remove every probe: grep for the marker tag and
delete. The rule exists because leftover instrumentation buries the
two-line real fix inside a twenty-line diff, ships debug noise (and
sometimes performance cost) to production, and desensitizes everyone to
debug output in logs.

The exception: a probe that proved *so* useful it should become permanent
observability. Promote it deliberately — proper log level, no `[DEBUG`
tag, named in the commit as an intentional addition — never by just
forgetting to delete it.
