# Aizen Control Plane v1.2 — Content Cleanup and Readable Dates

## Summary

Simplify the README while preserving the purple styling, compact layout, and
existing functionality.

## README and Configuration

- Change the disclosure title to **Inspect Engineer Resource**.
- Show only **Engineering**, **Infrastructure**, and **Artificial Intelligence**
  as capability headings. Remove slash suffixes while retaining each capability list.
- Remove the entire Kubernetes-inspired YAML manifest from the disclosure.
- Keep the featured project's name, summary, technologies, and links. Remove its
  three decision bullets and maintenance sentence.
- Use the exact link labels **Source**, **How It Works**, **Data & Last Sync**,
  and **Metric Definitions**. Preserve the telemetry explanatory sentence.
- Remove configuration fields and rendering code made unused by these deletions;
  retain PyYAML for loading configuration.
- Set `profile.version` to `"1.2"` and regenerate the hero.

## Date Presentation

- Format displayed dates with English month abbreviations: **07 Sep 2026**.
- Format synchronization timestamps as **07 Sep 2026, 16:23 UTC**.
- Apply formatting consistently to telemetry text, activity ranges, chart labels,
  SVG titles, and accessible descriptions.
- Share formatting helpers between generators, with explicit English month names
  so output does not depend on the machine's locale.
- Preserve ISO timestamps and dates in the JSON snapshot and API processing.
  Keep UTC grouping and existing metric semantics.
- Adjust date-label placement or wrap the synchronization line as needed within
  the existing 480 px panels.

## Validation and Delivery

- Test exact capitalization, retained capability lists and project links, and
  absence of removed manifest and copy.
- Test date formatting across month/year boundaries and synchronization timestamps,
  including accessible SVG text.
- Verify hero version v1.2, deterministic generation, and unchanged JSON data
  when rerendering an existing snapshot.
- Run existing tests and inspect panels at 320 and 480 px in both themes,
  including empty and populated activity states.
- Validate GitHub Markdown rendering and relative links; update maintenance
  documentation to reflect the simplified configuration.
- Deliver locally without commit or push.
