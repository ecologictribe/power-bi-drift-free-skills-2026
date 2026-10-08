# ADR-008: Generators must never delete the output root

- Status: accepted — 2026-10-08
- Applies to: `pbi-skills.md` §11, `build_from_spec.py` output guard

## Context

`build_from_spec.py` wiped its output directory before building. Invoked with
out=repo-root, it deleted `.git` (recovered from the public remote; working
tree survived). No data was pushed or lost, but the repo was unusable until
reconstructed via fresh clone + working-tree diff.

## Decision

1. Builders may delete **only** inside their own regenerable artifact dirs
   (`definition/pages/`). The output root itself is never removed.
2. Every generator entry point validates its output path: it must be the repo
   root (blessed trees) or a scratch dir beneath it — never `.git`, never
   outside the repo — and exits otherwise.
3. Recovery procedure (if it ever recurs): fresh public clone into
   `.quarantine/restore/`, transplant its `.git`, verify with `git status`.

## Consequences

- Destructive filesystem ops are now a skill-level concern, not just code care.
- `.quarantine/` doubles as the recovery workspace (gitignored by policy).
