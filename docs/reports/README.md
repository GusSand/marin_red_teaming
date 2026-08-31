# Reports

## Canonical living report

`phoenix-starling/index.html` is the reader-facing synthesis for the Phoenix-to-Starling research
program. It has a stable path and is updated throughout the project. It is not a second research log.

The evidence hierarchy remains:

1. raw or aggregate result artifacts;
2. pre-registered experiment files and independent verification;
3. the research journal and decision log;
4. the living report, which synthesizes the verified evidence for a reader.

## Update rule

Every current-task transition updates the report's visible progress table and these machine-readable
metadata fields:

- `marin-report-state` — `living` during the program, `final` only after the final review;
- `marin-report-updated` — the reconciliation date;
- `marin-current-task` and `marin-current-task-status` — must match `STATUS.md`.

Every result-producing task closure also updates the relevant claim, figure, limitations, and next-step
text. Verified results may enter the main narrative. Unverified work appears only in the progress section
and must be labelled `UNVERIFIED`. Failed and null results are included when they change the reader's
belief or a project decision.

The project-state checker rejects a report whose task pointer disagrees with `STATUS.md` or whose update
date predates it. This catches staleness; it does not certify editorial or scientific quality.

## Finalization and publication

The final report is the reviewed terminal state of the living report, not a rewrite assembled after the
experiments. At project closure:

1. reconcile every headline to durable evidence and verification;
2. remove operational progress language that no longer helps the reader;
3. set `marin-report-state` to `final`;
4. freeze an immutable dated snapshot;
5. publish both the dated snapshot and a stable `latest` alias from the same reviewed source.

Never edit the cloud copy by hand. Publication must be scripted and must not expose raw harmful responses,
credentials, private paths, or unapproved internal notes.

The dated `08-27_misinfo_refusal_vs_capability.html` file is the preserved foundation-study snapshot. Do
not update it; corrections and later evidence belong in the canonical living report.
