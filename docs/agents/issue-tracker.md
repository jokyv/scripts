# Issue tracker: GitHub

Issues and planning tickets live in GitHub Issues. Use `gh` for tracker operations.

## Wayfinding

- Map: one issue labeled `wayfinder:map` and `epic`.
- Child tickets: native GitHub sub-issues labeled `wayfinder:research`, `wayfinder:prototype`, `wayfinder:grilling`, or `wayfinder:task`.
- Before attaching children, verify parent is open, labeled `epic`, and the `ready-for-agent` label exists.
- Attach children using GitHub’s native sub-issue API. Use child REST database ID, not issue number or GraphQL node ID.
- Record blockers using native issue dependencies and blocker database IDs.
- Frontier: open, unblocked, unassigned child with lowest map order.
- Claim: assign ticket to `@me`.
- Resolve: comment with answer, close ticket, then add its decision summary and link to map.
