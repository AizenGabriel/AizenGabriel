# Aizen Control Plane v1.1 — Purple and compact presentation

## Direction

Evolve the profile with purple tones, less vertical space, and a more focused
reading experience. Feature the Control Plane itself as the first project and
explain how it works. Keep English copy and the existing Markdown, SVG, Python,
and GitHub Actions stack.

## Presentation

- Use purple-tinted neutral surfaces: dark background `#171321`, panels `#211A30`,
  and lavender accent `#C4B5FD`; light background `#FAF8FF`, panels `#F0EAFA`,
  and violet accent `#6D28D9`.
- Replace full-width images with centered, 480 px presentations that shrink on
  narrow screens. Do not enlarge SVG text to fill desktop README width.
- Redesign the hero around a 480 × 240 canvas, a 28 px name, an 18 px main line,
  and 14–16 px metadata.
- Display v1.1 using `profile.version` from the central YAML configuration.
- Add a small connected-node mark to the hero. Preserve subtle animation,
  adequate contrast, accessible text, and reduced-motion support.

## Content and architecture

- Use five primary sections: Identity, Featured Project, Architecture,
  Public Telemetry, and Connect.
- Condense identity and focus areas. Keep capabilities, the declarative manifest,
  and engineering principles inside a disclosure.
- Feature only Aizen Control Plane, with a short description, technologies,
  implementation decisions, and links to source and documentation. Do not invent
  projects, outcomes, or production experience.
- Document the implemented flow: YAML + GitHub API → Python → SVG/README →
  validation → Actions update.
- Replace the tall architecture ladder with a compact diagram connecting software,
  infrastructure, observability, and automation through feedback. Label AI as an
  exploration direction rather than an implemented production subsystem.
- Remove generic process rows. Mention Control Plane maintenance with the project;
  render an optional lab section only when concrete experiments are configured.
- Maintain version, featured project, and optional experiments in the central YAML.

## Telemetry and automation

- Rename the section to Public Telemetry and reduce spacing and metric size.
- When no events were observed, use a short explicit empty state with the period.
  Otherwise show a compact histogram.
- Preserve metric definitions, accessible snapshot, synchronization time, and
  failure-safe generation.
- Separate behavior tests from comparisons against existing generated files.
  Both workflows must generate identity before validating its output.
- Verify determinism using repeated generation from the same configuration,
  without requiring old files to already match updated YAML. Configuration-only
  changes must be accepted by the regeneration workflow.

## Validation and delivery

- Inspect SVGs at 320 and 480 px in light and dark themes, with no overflow or
  overlaps. Confirm desktop images do not exceed their 480 px presentation width.
- Check GitHub Markdown rendering, local links, and alternative text.
- Add tests for configurable version, empty/nonempty activity, and generation
  after a configuration-only change. Run existing API, escaping, determinism,
  and failure-preservation tests.
- Regenerate assets and update maintenance documentation. Commit, push, and
  inspection of the published profile are outside this local implementation.
