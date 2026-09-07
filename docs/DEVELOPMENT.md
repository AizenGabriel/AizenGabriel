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

## Metric contracts

- **Public repositories:** all public repositories owned by the configured account,
  including forks and archives, enumerated with pagination.
- **Pushed in N days:** owned, public, non-fork, non-archived repositories whose
  `pushed_at` is within the preceding N × 24 hours. This is repository recency,
  not a claim that the profile owner authored a commit.
- **Primary languages:** distinct non-null `language` values on public owned
  repositories, including forks and archives. This is not a complete language
  inventory or a byte distribution. Up to four common languages appear in the
  card; the complete counts are in the JSON snapshot.
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
inputs on `main`. It checks out the default branch, tests, generates, and stages
only README and assets. `contents: write` enables the bot commit/push. No PAT,
external service or hosting is required. Generated paths do not trigger refresh;
the workflow token also suppresses recursive push workflows. Runs are serialized.
A concurrent human push can reject the bot push safely; rerun after that failure.
Branch protection must permit the bot's direct generated commits for this workflow
to operate. The schedule becomes active after the workflow is on the default
branch and GitHub Actions is enabled.

`validate.yml` checks pull requests without write permissions or API access.
API and rendering failures return a nonzero exit code before replacing any output.
Each output is written to a temporary sibling and replaced atomically. A filesystem
failure between replacements is not a multi-file transaction; the failing workflow
never reaches the commit step. Previously committed assets remain available.

## Visual validation

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
