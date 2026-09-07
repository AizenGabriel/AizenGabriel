# Maintaining the control plane

`config/profile.yaml` is the manually maintained profile source. The English copy
follows the specification. AI capabilities are explicitly interests and experiments.
Only the configured GitHub contact is included. MIT is the initial project license.
The canonical specification remains in `docs/specs/`; root `SPEC.md` links to it.

## Generate locally

Python 3.13 is used in CI; Python 3.10+ is sufficient for the scripts.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python scripts/generate_profile.py
python scripts/generate_telemetry.py
python -m unittest discover -s tests -v
```

PyYAML is the only runtime dependency. API access, rendering and writes otherwise
use the standard library. Telemetry uses `GITHUB_TOKEN` if present; unauthenticated
public API access also works with lower rate limits. Never put credentials in YAML.
`generate_activity.py` can redraw activity offline from `telemetry.json`.
Static identity generation does not require network access.

## How this project works

Aizen Control Plane is a small profile-as-code project. Its scope is the profile
itself; the conceptual architecture in the README describes an engineering
approach, not a claim that this repository runs Kubernetes or an AI service.

```text
profile.yaml ────────────────→ identity generator ─→ README + static SVGs
GitHub public REST API ──────→ telemetry generator → SVGs + JSON snapshot
                                     │
GitHub Actions: generate identity → validate → collect/render → commit changed files
```

The profile uses one declarative source for identity and project copy. Python
escapes SVG text, renders deterministic assets, and replaces outputs atomically.
The workflow runs on a schedule; failed API requests retain the last valid output.
A snapshot can also be rendered offline without changing its synchronization time.
These choices demonstrate automation, reproducibility, and explicit data limits
without adding an application server or external hosting.

### Content configuration

- `profile.version` is a quoted version string, currently `"1.1"`. It controls the
  visible hero version; it is separate from the engineer manifest API version.
- `featured_project` supplies the name, summary, technologies, decisions,
  maintenance note, source URL, and documentation link. The Control Plane is the
  only configured project.
- `experiments` defaults to an empty list. Each real experiment has `name`,
  `question`, and `url`; an empty list omits the lab block.
- `architecture.nodes` defines four clockwise feedback-loop labels, and
  `architecture.exploration` labels the dashed exploration branch.
- Capabilities and principles remain available in the engineer disclosure.

The v1.1 implementation plan is recorded in
[the English plan](<specs/PLAN.md — Aizen Control Plane v1.1.md>).

## Metric contracts

- **Public repositories:** all public repositories owned by the configured account,
  including forks and archives, enumerated with pagination.
- **Pushed in N days:** owned, public, non-fork, non-archived repositories whose
  `pushed_at` is within the preceding N × 24 hours. This is repository recency,
  not a claim that the profile owner authored a commit.
- **Primary languages:** distinct non-null `language` values on public owned
  repositories, including forks and archives. This is not a complete language
  inventory or a byte distribution. The card shows the distinct-language count; the complete per-language
  repository counts are in the JSON snapshot.
- **Activity:** deduplicated public events returned by the user public events API,
  grouped into N UTC calendar days including today. The endpoint supplies at most
  300 events from the last 30 days and may lag. A zero means no observed returned
  events, not proven inactivity. A full 300-event response is flagged as potentially
  truncated. Events are never presented as commits or contribution totals.
- **Last successful sync:** actual UTC collection time. A successful new fetch
  changes this field even if counts are unchanged. Re-rendering the same snapshot
  is byte-identical; the workflow only commits a nonempty staged diff.

API references: [repository listing](https://docs.github.com/en/rest/repos/repos#list-repositories-for-a-user),
[public events and limits](https://docs.github.com/en/rest/activity/events#list-public-events-for-a-user),
[workflow token](https://docs.github.com/en/actions/concepts/security/github_token).

## Automation and recovery

`update-profile.yml` runs daily at 08:23 UTC, manually, and on changes to generation
inputs on `main`. It checks out the default branch, generates identity, tests, refreshes telemetry, and stages
only README and assets. `contents: write` enables the bot commit/push. No PAT,
external service or hosting is required. Generated paths do not trigger refresh;
the workflow token also suppresses recursive push workflows. Runs are serialized.
A concurrent human push can reject the bot push safely; rerun after that failure.
Branch protection must permit the bot's direct generated commits for this workflow
to operate. The schedule becomes active after the workflow is on the default
branch and GitHub Actions is enabled.

`validate.yml` checks pull requests without write permissions or API access.
Both workflows generate identity before testing. Reproducibility tests render to a
temporary directory, change configuration, and render twice again, checking bytes
and unchanged modification times. They do not require previously committed assets
to match new YAML. A configuration-only change therefore passes validation and can
be rendered and committed by the refresh workflow after merge.
API and rendering failures return a nonzero exit code before replacing any output.
Each output is written to a temporary sibling and replaced atomically. A filesystem
failure between replacements is not a multi-file transaction; the failing workflow
never reaches the commit step. Previously committed assets remain available.

## Visual validation

README images have a 480 px presentation width instead of scaling to full desktop
width; GitHub's responsive image rules constrain them on smaller screens. The hero
is 480 × 240 and the architecture is 480 × 248. Purple/light-lavender accents share
one SVG stylesheet. Empty activity uses a short message and date range instead of
a tall empty chart; observed activity uses a compact histogram.

SVGs use native text, accessible titles/descriptions, fixed viewBox coordinates,
light/dark CSS and reduced-motion support. No remote fonts, raster dependencies,
JavaScript or hosted widgets are involved. Markdown repeats the identity and
capabilities; the JSON snapshot exposes text equivalents of the metrics.

For visual QA, optionally install CairoSVG in a separate environment and render
assets at desktop and narrow widths. Browser or GitHub checks should include light
and dark themes. The only animation is a slow operational pulse; all content
remains readable with animation disabled. GitHub sanitization and image caching
can affect theme/animation behavior, so inspect the published profile after push.

Initial validation (2026-09-07): 12 offline tests passed. Live public REST collection
produced the checked-in snapshot. GitHub's Markdown API preserved the four images,
eight sections, manifest disclosure and image alternative text. SVG raster previews
were inspected at 640 px and 320 px with light/dark styles; the final layout was
adjusted for narrow screens. Theme variants were explicitly selected for CairoSVG,
which does not simulate browser color-scheme negotiation. The deployed profile and
scheduled workflow still require inspection after the files are pushed to GitHub.

v1.1 validation (2026-09-07): 15 offline tests pass, including a YAML-only change,
version propagation, and empty/nonempty activity. Light/dark previews were inspected
at 480 and 320 px, plus a nonempty activity preview using a temporary test sample.
The production snapshot was retained unchanged; restyling does not represent a new
API synchronization. GitHub's Markdown API preserved all four 480 px image widths,
the five primary sections, alternative text, and the engineer disclosure. Final
published layout and workflow execution remain checks to perform after push.
