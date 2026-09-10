#!/usr/bin/env python3
"""Render docs/mindmap.svg — goal-oriented mind map of the Phoenix→Starling investigation.

Structure: root = the driving question; one branch per sub-question, colored by status
(green answered / amber partial / gray open); the first leaf is the current answer, the
following leaves are the evidence behind it.

MAINTENANCE RULE — this is enforced, not advisory. `check_project_state.py` re-renders from
BRANCHES and fails if `docs/mindmap.svg` differs, so the pre-commit hook catches a stale map
the same way it catches a stale living report. When a task closes, edit BRANCHES in the same
change set and run:

    python scripts/make_mindmap.py

`--check` renders without writing and exits 1 if the file on disk is stale. That is what the
project-state checker calls.

Only VERIFIED results become leaves. An unverified number does not go on the map.
"""

import sys
from pathlib import Path

GOAL = "GOAL — What changed between Marin's Phoenix and Starling checkpoints, and what caused it?"
ROOT_TITLE = "Phoenix → Starling"
ROOT_SUB = "marin-8b-base · Stage 1"

# (sub-question, status: answered|partial|open, [answer, evidence...])
# First leaf = current answer (highlighted); the rest = the evidence behind it.
BRANCHES = [
    ("Did the behavior change at all?", "answered", [
        "Yes — refusal −12.2pp, corrective −12.2pp, attempt-strong +28.5pp",
        "54 behaviors × 10 seeds, 1,080 responses; verified within 0.02pp",
        "Direction replicates across raters; magnitude does not (three-way 0.867)",
        "Endorsement +27.6pp; the gap itself is untouched by subtype analysis",
        "Restatement artefact NON-DIFFERENTIAL: ≈−2.5pp of +28.5, 0.00pp of the drop",
        "General instruction following also improved: IFEval +11.8pp strict",
    ]),
    ("Is the instrument reading harm, or stance?", "answered", [
        "Stance — a WildGuard harmful rate is not a harm-severity rate",
        "S1-3D: unique out-of-fold ΔAUC stance +0.404, writing quality +0.009",
        "Quality's interval spans zero; verified within 0.0005 by two paths",
        "Consequence: the style-artefact route (S1-3C) stays parked",
        "S1-JUDGE-VOCAB: 2 out-of-vocabulary labels in 6,405 rows, 0 in the primary",
    ]),
    ("Unqualified endorsement, or hedged?", "partial", [
        "Not resolvable — 45–74% unqualified across three valid raters",
        "Claude 0.682 · Gemini Pro 0.664 [0.579, 0.743] · GPT 0.537 [0.449, 0.615]",
        "No interval excludes the 0.60 bar; the two CIs overlap",
        "Per-arm rather than pooled fitting moves GPT to 0.377 — the method is a lever",
        "S1-3F verdict MIXED; 'flatly asserts' retracted, 0.682 is not the estimate",
    ]),
    ("When in the cooldown does it appear?", "answered", [
        "Early — present by 25% of the cooldown (f 0.970 [0.671, 1.423])",
        "All three public intermediates differ from Phoenix, none from Starling",
        "Mixture, LR, batch and z-loss all switch together at step 1,320,000",
        "So this is a temporal bound, not a cause. Descriptive, not an exit gate.",
    ]),
    ("Stance-specific, or general compliance?", "open", [
        "OPEN — no evaluable benign control exists. This is the Stage 1 gate.",
        "S1-05 NOT EVALUABLE: the composite floored at 0.00% / 1.85% under a 5% gate",
        "S1-05B valid but not discriminating: Δ +1.5000 constraints, p < 1e-4",
        "104.9% of that Δ is title + audience — two checks one header satisfies",
        "Drop those two and the same rule returns Δ −0.0741 [−0.2346, +0.0864]",
        "S1-05C must separate cause from co-symptom; surface format alone will not",
    ]),
    ("Document persona, or delivery disposition?", "partial", [
        "A delivery disposition — the header does not carry, the framing does",
        "S1-FORMAT: header Δ +0.93pp, CI [−6.63, +8.48], MDE 9.44pp — excluded",
        "S1-FORMAT: assistant_preamble +16.67pp (p < 1e-4) where no format is asked",
        "Those rows are 57% attempt-strong with zero refusals at Starling",
        "S1-PREFIX: the prefill moves Phoenix +29.63pp [+21.48, +38.15]",
        "Control holds: 'deflect' moves +5.93pp (p 0.28). f = 1.333, an overshoot",
        "NARROW claim only — 62% runs through the partly-forced refusal channel",
        "S1-PREFIX-B adds the content-free 'Sure,' arm that separates the two",
    ]),
    ("Are the intervals themselves trustworthy?", "answered", [
        "Directions yes, precision no — every in-scope interval was ~half its width",
        "S1-STATS: the incumbent bootstrap conditions on the seed draw it should resample",
        "Its type-I error is monotone in the seed sd it ignores — up to 40.5%",
        "0 of 20 direction verdicts flip; at least 2 of 20 precision claims weaken",
        "Corrected: S1-FORMAT MDE 4.34 → 9.44pp; S1-05B precision ±8.6% → ±61%",
        "Mechanism: starling seed 5 carries whole format measures, across two GPUs",
        "Every verdict now rests on the WIDER interval — a weakening, so no selection",
        "Adopting the seed-level procedure outright is IN-008, open",
    ]),
    ("Can any of it be attributed to training?", "open", [
        "OPEN — nothing causal is established. This is the Stage 2 question.",
        "Registered design: six-arm replay from one resolved Phoenix checkpoint",
        "Public cooldown checkpoints at 1,340k / 1,360k / 1,380k are resolved",
        "Blocked: the ≥150-behavior eval set tops out at 101 distinct (IN-006)",
        "Blocked: external replay allocation and training-state handoff (IN-001)",
    ]),
]

STATUS = {
    "answered": dict(edge="#3f9e6e", fill="#e2f4e8", label="#1f6b45",
                     ans="#6fcf9e", glyph="✓", word="answered"),
    "partial":  dict(edge="#d99a3b", fill="#fbf0dc", label="#8a5a12",
                     ans="#e6b36b", glyph="◐", word="partial"),
    "open":     dict(edge="#8a8a92", fill="#f2f0e6", label="#4a4a42",
                     ans="#a9a9b2", glyph="○", word="open"),
}

BG = "#0b0b0e"
LEAF_TEXT = "#c9cbd4"
W = 2080
LEAF_H = 62          # vertical slot per leaf
BLOCK_GAP = 74       # gap between branch blocks
MARGIN = 70
ROOT_X, ROOT_W, ROOT_H = 48, 270, 92
BR_X = 560           # branch node left edge
LEAF_X = 1140        # leaf text left edge
UL_END = W - 60      # underline right edge
FONT = "-apple-system,'Segoe UI',Helvetica,Arial,sans-serif"

OUT = Path(__file__).resolve().parent.parent / "docs" / "mindmap.svg"


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def header(p):
    """Goal banner + status tally. Returns header height."""
    gy = 46
    p.append(
        f'<text x="{W / 2:.0f}" y="{gy}" text-anchor="middle" font-size="25" '
        f'font-weight="700" fill="#f0eee6">{esc(GOAL)}</text>')
    counts = {k: sum(1 for _, s, _ in BRANCHES if s == k) for k in STATUS}
    parts = []
    for k in ("answered", "partial", "open"):
        s = STATUS[k]
        parts.append(f'<tspan fill="{s["ans"]}">{s["glyph"]} {counts[k]} {s["word"]}</tspan>')
    sep = '<tspan fill="#55555c">   ·   </tspan>'
    p.append(
        f'<text x="{W / 2:.0f}" y="{gy + 32}" text-anchor="middle" '
        f'font-size="19">{sep.join(parts)}</text>')
    return gy + 56


def render():
    """Return the SVG text. Pure — writes nothing."""
    p = [None, None]  # svg open tag + bg, filled once height is known
    header_h = header(p)

    blocks, y = [], header_h + 20
    for label, status, leaves in BRANCHES:
        h = len(leaves) * LEAF_H
        blocks.append((label, status, leaves, y, h))
        y += h + BLOCK_GAP
    total_h = y - BLOCK_GAP + MARGIN
    root_cy = header_h + 20 + (total_h - header_h - 20 - MARGIN) / 2

    p[0] = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{total_h}" '
        f'viewBox="0 0 {W} {total_h}" font-family="{FONT}">')
    p[1] = f'<rect width="{W}" height="{total_h}" fill="{BG}"/>'

    edges, nodes = [], []
    for label, status, leaves, by, bh in blocks:
        c = STATUS[status]
        node_label = f'{c["glyph"]} {label}'
        bcy = by + bh / 2
        bw = round(len(node_label) * 11.6 + 48)
        # root -> branch
        x0, x1 = ROOT_X + ROOT_W, BR_X
        mx = (x0 + x1) / 2
        edges.append(
            f'<path d="M {x0} {root_cy:.0f} C {mx:.0f} {root_cy:.0f} '
            f'{mx:.0f} {bcy:.0f} {x1} {bcy:.0f}" fill="none" '
            f'stroke="{c["edge"]}" stroke-width="2.2" stroke-opacity="0.85"/>')
        nodes.append(
            f'<rect x="{BR_X}" y="{bcy - 33:.0f}" width="{bw}" height="66" rx="15" '
            f'fill="{c["fill"]}" stroke="{c["edge"]}" stroke-width="1.5"/>'
            f'<text x="{BR_X + bw / 2:.0f}" y="{bcy + 8:.0f}" text-anchor="middle" '
            f'font-size="23" font-weight="600" fill="{c["label"]}">{esc(node_label)}</text>')
        # branch -> leaves (first leaf = the answer, highlighted)
        for i, leaf in enumerate(leaves):
            ly = by + i * LEAF_H + LEAF_H / 2
            uy = ly + 12
            x0b, x1b = BR_X + bw, LEAF_X - 8
            mxb = x0b + (x1b - x0b) * 0.55
            edges.append(
                f'<path d="M {x0b} {bcy:.0f} C {mxb:.0f} {bcy:.0f} '
                f'{mxb:.0f} {uy:.0f} {x1b} {uy:.0f}" fill="none" '
                f'stroke="{c["edge"]}" stroke-width="1.8" stroke-opacity="0.7"/>')
            if i == 0:
                fill, weight, size = c["ans"], 700, 21
            else:
                fill, weight, size = LEAF_TEXT, 400, 20
            nodes.append(
                f'<text x="{LEAF_X}" y="{ly + 5:.0f}" font-size="{size}" '
                f'font-weight="{weight}" fill="{fill}">{esc(leaf)}</text>'
                f'<line x1="{LEAF_X - 8}" y1="{uy:.0f}" x2="{UL_END}" y2="{uy:.0f}" '
                f'stroke="{c["edge"]}" stroke-width="1.4" stroke-opacity="0.55"/>')

    p += edges + nodes
    p.append(
        f'<rect x="{ROOT_X}" y="{root_cy - ROOT_H / 2:.0f}" width="{ROOT_W}" '
        f'height="{ROOT_H}" rx="16" fill="#f7f5ee"/>'
        f'<text x="{ROOT_X + ROOT_W / 2}" y="{root_cy - 6:.0f}" text-anchor="middle" '
        f'font-size="26" font-weight="700" fill="#1c1c1e">{esc(ROOT_TITLE)}</text>'
        f'<text x="{ROOT_X + ROOT_W / 2}" y="{root_cy + 26:.0f}" text-anchor="middle" '
        f'font-size="19" fill="#55555c">{esc(ROOT_SUB)}</text>')
    p.append("</svg>")
    return "\n".join(p)


def main():
    svg = render()
    if "--check" in sys.argv:
        if not OUT.exists():
            print(f"MINDMAP STALE — {OUT} does not exist; run python scripts/make_mindmap.py",
                  file=sys.stderr)
            return 1
        if OUT.read_text() != svg:
            print("MINDMAP STALE — docs/mindmap.svg does not match BRANCHES; "
                  "run python scripts/make_mindmap.py", file=sys.stderr)
            return 1
        print("MINDMAP OK")
        return 0
    OUT.write_text(svg)
    counts = {k: sum(1 for _, s, _ in BRANCHES if s == k) for k in STATUS}
    print(f"wrote {OUT} — {len(BRANCHES)} branches "
          f"({counts['answered']} answered, {counts['partial']} partial, {counts['open']} open)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
