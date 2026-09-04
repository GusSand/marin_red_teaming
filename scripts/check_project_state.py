#!/usr/bin/env python3
"""Validate the small active project-control surface.

This intentionally ignores the legacy backlog and inbox history. It checks only the
machine-marked active tables and the authoritative current-task pointer in STATUS.md.
"""

from __future__ import annotations

import argparse
import re
import sys
from datetime import date, datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ALLOWED_TASK_STATUSES = {"READY", "IN_PROGRESS", "BLOCKED", "PARKED", "DONE"}
ALLOWED_REPORT_STATES = {"living", "final"}
LIVING_REPORT = "docs/reports/phoenix-starling/index.html"


def fail(message: str) -> None:
    print(f"PROJECT STATE FAILED — {message}", file=sys.stderr)
    raise SystemExit(1)


def read(relative: str) -> str:
    path = ROOT / relative
    if not path.is_file():
        fail(f"missing {relative}")
    return path.read_text(encoding="utf-8")


def marked(text: str, start: str, end: str, source: str) -> str:
    if text.count(start) != 1 or text.count(end) != 1:
        fail(f"{source} must contain exactly one {start}/{end} marker pair")
    body = text.split(start, 1)[1].split(end, 1)[0]
    if not body.strip():
        fail(f"{source} active block is empty")
    return body


def table_rows(block: str, source: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in block.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if not cells or cells[0] in {"ID", "---"} or set(cells[0]) == {"-"}:
            continue
        rows.append(cells)
    if not rows:
        fail(f"{source} has no active rows")
    return rows


def field(status: str, label: str) -> str:
    match = re.search(rf"^- \*\*{re.escape(label)}:\*\*\s+`?([^`\n]+)`?\s*$", status, re.MULTILINE)
    if not match:
        fail(f"STATUS.md is missing '{label}'")
    return match.group(1).strip()


def meta(html: str, name: str) -> str:
    pattern = rf'<meta\s+name="{re.escape(name)}"\s+content="([^"]+)"\s*/?>'
    match = re.search(pattern, html, re.IGNORECASE)
    if not match:
        fail(f"{LIVING_REPORT} is missing meta {name!r}")
    return match.group(1).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--require-in-progress",
        action="store_true",
        help="fail unless the current task is IN_PROGRESS (used by GPU submission)",
    )
    args = parser.parse_args()

    status = read("STATUS.md")
    backlog = read("BACKLOG.md")
    inbox = read("INBOX.md")
    read("docs/PROJECT_OPERATING_RULES.md")
    report = read(LIVING_REPORT)

    current_task = field(status, "Current task")
    current_status = field(status, "Task status")
    updated_raw = field(status, "Last updated")

    try:
        updated = datetime.strptime(updated_raw, "%Y-%m-%d").date()
    except ValueError:
        fail("STATUS.md Last updated must be YYYY-MM-DD")
    age = (date.today() - updated).days
    if age > 7:
        fail(f"STATUS.md is stale ({age} days old); reconcile it before work continues")
    if age > 3:
        print(f"PROJECT STATE WARNING — STATUS.md is {age} days old", file=sys.stderr)
    if age < 0:
        fail("STATUS.md Last updated is in the future")

    report_state = meta(report, "marin-report-state")
    report_updated_raw = meta(report, "marin-report-updated")
    report_task = meta(report, "marin-current-task")
    report_task_status = meta(report, "marin-current-task-status")
    if report_state not in ALLOWED_REPORT_STATES:
        fail(f"living report has invalid state {report_state!r}")
    try:
        report_updated = datetime.strptime(report_updated_raw, "%Y-%m-%d").date()
    except ValueError:
        fail("living report marin-report-updated must be YYYY-MM-DD")
    if report_updated < updated:
        fail("living report predates STATUS.md; reconcile its progress before committing")
    if report_updated > date.today():
        fail("living report update date is in the future")
    if report_task != current_task or report_task_status != current_status:
        fail(
            "living report current-task metadata must match STATUS.md "
            f"({report_task}:{report_task_status} != {current_task}:{current_status})"
        )

    task_rows = table_rows(
        marked(backlog, "<!-- ACTIVE_TASKS_START -->", "<!-- ACTIVE_TASKS_END -->", "BACKLOG.md"),
        "BACKLOG.md",
    )
    task_map: dict[str, list[str]] = {}
    in_progress: list[str] = []
    for row in task_rows:
        if len(row) != 6:
            fail(f"BACKLOG.md row {row[0]!r} must have 6 columns")
        task_id, task_status, owner, outcome, next_action, evidence = row
        if task_id in task_map:
            fail(f"duplicate active task ID {task_id}")
        if task_status not in ALLOWED_TASK_STATUSES:
            fail(f"task {task_id} has invalid status {task_status}")
        if not all((owner, outcome, next_action, evidence)):
            fail(f"task {task_id} has an empty contract field")
        # A BLOCKED task must name what unblocks it. Two legitimate kinds of blocker:
        #   - a person must act        -> an INBOX ID (IN-nnn)
        #   - a sibling task must land -> one or more task IDs from this same table
        # Requiring an INBOX ID for a purely task-dependent blocker forced such tasks to be
        # mislabelled READY, which is what S1-SYNTH was doing (Gus, 2026-09-04). Both forms are
        # validated below: referenced INBOX IDs must be live, and referenced task IDs must exist
        # and must not already be DONE.
        if task_status == "BLOCKED" and not re.search(r"`?(IN-\d+|S\d[\w-]*|PM-\d+|S2-\d+)`?", next_action):
            fail(f"blocked task {task_id} must name an INBOX ID or a blocking task ID in Next action")
        if task_status == "IN_PROGRESS":
            in_progress.append(task_id)
        task_map[task_id] = row

    if len(in_progress) > 1:
        fail(f"WIP limit exceeded: {', '.join(in_progress)} are IN_PROGRESS")
    if current_task not in task_map:
        fail(f"STATUS.md current task {current_task} is not in the active backlog")
    if current_status != task_map[current_task][1]:
        fail(
            f"STATUS.md says {current_task} is {current_status}, "
            f"but BACKLOG.md says {task_map[current_task][1]}"
        )
    if current_status in {"BLOCKED", "PARKED", "DONE"}:
        fail(f"STATUS.md current task cannot be {current_status}")
    if args.require_in_progress and current_status != "IN_PROGRESS":
        fail("GPU submission requires the current task to be IN_PROGRESS")
    if in_progress and in_progress != [current_task]:
        fail(f"the IN_PROGRESS task must be STATUS.md current task {current_task}")

    inbox_rows = table_rows(
        marked(inbox, "<!-- ACTIVE_INBOX_START -->", "<!-- ACTIVE_INBOX_END -->", "INBOX.md"),
        "INBOX.md",
    )
    inbox_ids: set[str] = set()
    for row in inbox_rows:
        if len(row) != 6:
            fail(f"INBOX.md row {row[0]!r} must have 6 columns")
        inbox_id = row[0]
        if inbox_id in inbox_ids:
            fail(f"duplicate active inbox ID {inbox_id}")
        if not inbox_id.startswith("IN-"):
            fail(f"active inbox ID {inbox_id!r} must start with IN-")
        if not all(row[1:]):
            fail(f"inbox item {inbox_id} has an empty field")
        inbox_ids.add(inbox_id)

    for task_id, row in task_map.items():
        if row[1] != "BLOCKED":
            continue
        referenced = set(re.findall(r"IN-\d+", row[4]))
        missing = referenced - inbox_ids
        if missing:
            fail(f"blocked task {task_id} references missing inbox IDs: {', '.join(sorted(missing))}")
        # Task-dependency blockers: every named task must exist, must not be this task, and must not
        # already be DONE -- a task blocked on finished work is a stale state, not a valid blocker.
        named = {t for t in re.findall(r"`([A-Z0-9][\w-]*)`", row[4])
                 if t in task_map and t != task_id}
        finished = sorted(t for t in named if task_map[t][1] == "DONE")
        if finished:
            fail(f"blocked task {task_id} names already-DONE blockers: {', '.join(finished)}")
        if not referenced and not named:
            fail(f"blocked task {task_id} names no live INBOX ID and no live blocking task")

    print(
        f"PROJECT STATE OK — current={current_task}:{current_status}; "
        f"tasks={len(task_rows)}; inbox={len(inbox_rows)}; wip={len(in_progress)}; "
        f"report={report_state}@{report_updated_raw}"
    )


if __name__ == "__main__":
    main()
