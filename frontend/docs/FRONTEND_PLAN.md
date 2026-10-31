# ImpactOS frontend plan

> Historical initial plan. The implementation now uses an editorial public site and a black app workspace. See README.md, DESIGN.md, and APP_DESIGN.md for the current routes, theme, and behavior.

28 October 2026 · Scope: frontend only · Status: design direction and clickable concept prepared.

## Product goal

Help an engineer move from a proposed API change to a reviewable impact report, with the evidence always one click away. The home page explains this workflow; the application helps perform it.

The primary journey is: Home → Get started → authenticated workspace (or clearly marked demo) → new investigation → choose baseline/proposed change → review → run → report → inspect evidence and dependency paths.

The current concept opens the demo directly. Production Get started checks session state: unauthenticated visitors go to sign-in, new members choose/create an authorized workspace through the backend, and returning members reach investigations. “View example” is a separate path that always opens the synthetic report without requiring sign-in.

## Responsibility boundary

**Frontend work:** public pages, app shell, forms, client validation, responsive layouts, navigation, graph presentation, diff presentation, source viewer, report presentation, empty/loading/error states, accessible interactions, API adapter, and integration documentation.

**Jayat's work:** FastAPI endpoints, OIDC/session implementation, actual authorization, tenant isolation, file processing/storage, queues, graph extraction, retrieval/reranking, LLM calls, persistence, deployment, infrastructure, and backend observability.

Frontend permission-aware controls improve usability; the server still decides every authorization outcome. The frontend displays server findings and never manufactures an impact assessment. No Next.js database layer, AI proxy, ingestion worker, or substitute backend will be added as part of this task.

## Design concept

Bright white canvas, deep ink type, pine-green actions, delicate gray dividers, modest corners, and generous whitespace on the public page. The workspace uses compact rows and a persistent evidence panel. Typography and alignment do most of the work.

The homepage headline is “See beyond the diff.” Supporting copy: “Trace an API change through services, customer integrations, and source documents. Review the evidence before you ship.” A concrete sample report sits alongside the headline. No invented customers, testimonials, uptime claims, ROI statistics, or generic AI capability carousel.

## Page map and primary behavior

| Route | Purpose | Primary action |
|---|---|---|
| `/` | Introduce ImpactOS using a real product-shaped example | Get started |
| `/demo` | Clearly labeled synthetic investigation | Inspect example evidence |
| `/sign-in` | Identity-provider handoff and expired-session recovery | Continue with configured provider |
| `/onboarding` | Authorized workspace selection and initial setup | Open workspace |
| `/app/investigations` | Searchable list, useful status filters, recent work | New investigation |
| `/app/investigations/new` | Scope and describe a proposed change | Review investigation |
| `/app/investigations/[id]` | Progress, report, findings, paths, evidence | Inspect a finding |
| `/app/sources` | Upload/list source documents and versions | Add sources |
| `/app/sources/[id]` | Versions, indexing status, authorized source detail | Inspect a version |
| `/app/dependencies` | Explore bounded entity relationships and provenance | Find an entity |
| `/app/settings` | Workspace details and connection status supported by backend | Save supported settings |

Settings initially stays small. No billing screens, team invitations, connector toggles, or fake integrations until a corresponding server capability exists.

## Homepage composition

1. Restrained navigation: wordmark, Workflow, Evidence, Get started. Product links scroll to meaningful sections.
2. Asymmetric hero: specific headline and short explanation on the left, sample change and report on the right. Primary Get started and secondary View example.
3. Workflow section: one continuous change → consumer → customer path paired with a short explanation of provenance.
4. Evidence section: one expanded source excerpt, a visible immutable version, and clear distinctions between confirmed dependency, possible impact, and unknown.
5. Compact closing invitation and footer. No unrelated feature grid or fake pricing.

The landing example and app demo share fixture data so counts, findings, and citations remain consistent. Explicitly label the fictional dataset. A tiny decorative mark is acceptable; large generated hero artwork does not help explain the product.

## Application screen details

### Investigations

Use a list/table of title, project, status, author if available, and updated time. Put filters in the toolbar; persist search/filter state in URL parameters. Empty state explains the first step and offers an example. Avoid top-of-page vanity metric cards.

### New investigation

Form sections: project, baseline snapshot, proposed specification/diff, optional question, and review. Start with two OpenAPI file inputs or existing version selectors, plus a change description. Client validation catches missing inputs, obvious file-type errors, and configured size limits. Server validation handles content validity and authority.

Preserve form values after a failed submission; never lose the user's work on a transient error. Show which files/snapshot will be used before submission. Do not advertise live GitHub connection until the backend supports it.

### Progress and report

Use the same route through queued/running/completed/failed/cancelled states. Show the latest server stage and last update rather than invented percentages. Initial implementation polls the job endpoint with backoff and cleanup; SSE can be added if supported later.

Completed desktop layout: persistent app sidebar; report heading and snapshot metadata; findings/paths/checklist tabs; selectable finding list; source evidence inspector. Selection is linkable through query parameters so someone can reopen the same authorized finding.

Each finding shows the affected entity, supported claim, status classification, explanation, source reference, and relationship path when supplied. Severity and certainty are different fields. Never draw arbitrary confidence percentages. An incomplete investigation must remain visibly incomplete even when partial findings exist.

### Evidence inspector

Show document name, version/commit, line/page/JSON-pointer location, exact excerpt, and why it is cited. Accessible source navigation retains the current investigation. Longer source viewing can open a focused dialog with keyboard focus management. Permission-denied and deleted-source states must not expose cached content.

Use a code-like treatment only for code/specs. Human documents should read like documents. Contract material is labeled for review; the interface does not turn it into a legal decision.

### Dependency view

Start with a bounded, readable path view rather than a giant force-directed graph. Support selecting an entity, filtering entity types, and inspecting the source behind an edge. Offer an equivalent list/table for keyboard and mobile use. Every shown relationship must originate in returned data.

### Sources

Show file name/type, active version, indexing state, updated time, and supported actions. Upload controls show selected files and progress provided by upload callbacks. Indexing status is separate from transfer progress. Failed indexing offers retry only if permitted. Replacement versions do not look active until the backend activates them.

## Frontend architecture

Use Next.js App Router + TypeScript. CSS variables and CSS Modules define the visual language; component primitives can provide accessible dialogs/menus without dictating the design. Start with simple SVG for the small path view; adopt a graph library only if interaction scope warrants it.

Recommended organization:

```text
frontend/
  src/app/(marketing)/
  src/app/(auth)/
  src/app/app/
  src/components/ui/
  src/components/layout/
  src/features/investigations/
  src/features/sources/
  src/features/dependencies/
  src/contracts/
  src/lib/api/            interface + HTTP adapter
  src/lib/demo/           explicit fixture adapter
  src/styles/
  public/
  tests/
  docs/
  design/
```

Routing conventions follow the [Next.js project structure documentation](https://nextjs.org/docs/app/getting-started/project-structure). Pin supported package versions and commit the lockfile when scaffolding the real app. The concept currently has no package dependencies.

Demo mode must be explicit and isolated. An unavailable backend is an error, never a reason to silently switch to convincing sample findings. Real-mode requests use one data adapter. The mock and HTTP adapters return the same contracts, so backend integration does not require rewriting screens.

## State and accessibility checklist

- Loading, empty, error, offline/disconnected, forbidden, session-expired, partial-result, and ready states for relevant screens.
- Visible focus, labeled controls, native buttons/links, useful headings, keyboard access, reduced-motion support, and readable contrast.
- Dialogs manage initial focus, contain focus, close with Escape, and return focus to the invoking control, following [WAI guidance](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/).
- Desktop at 1440/1280: sidebar plus content and evidence. Tablet: collapsible sidebar and evidence drawer. Mobile at 390/360: one content column with a full-screen source view.
- No horizontal page overflow; long paths and IDs wrap or truncate with accessible full text. Diff/code panes may scroll independently.
- Tables retain semantics; smaller layouts offer readable summaries without hiding essential status or actions.
- Announce job-state changes politely, not every timer tick. Preserve focus while polling.
- Reset private UI caches on sign-out/workspace change; do not store private reports or tokens in localStorage by default.

## Implementation sequence

Estimates are focused build sessions, not guaranteed calendar completion. The backend work can proceed independently against the proposed contract.

| Session | Deliverable | Check |
|---|---|---|
| 1 | Scaffold Next.js, tokens, typography, shared primitives | Builds; buttons/inputs have all core states |
| 2 | Responsive public homepage and explicit demo entry | CTA routing, mobile nav, and all section links work |
| 3 | Application shell, investigations list, filters, empty states | URL-driven selection and predictable navigation |
| 4 | New-investigation form and review screen | Validation, preserved input, fixture submission flow |
| 5 | Report and evidence inspector | Every sample citation opens the matching source |
| 6 | Dependency paths and source/version screens | Readable paths, upload/indexing states, version clarity |
| 7 | Auth UI boundaries and HTTP adapter | Contract errors and session-expiry handled consistently |
| 8 | Responsive, keyboard, contrast, and interaction QA | Core journey passes on desktop and mobile |
| 9–10 if needed | Connect your ready endpoints and fix mismatches | No demo results leak into live mode |

## Definition of done

All agreed frontend screens exist; the core journey works with explicit demo fixtures; real API wiring is centralized and documented; forms and async states behave correctly; evidence selection is consistent; the UI passes responsive and keyboard checks; production build and core interaction tests pass. Live backend functionality is verified only once your services are available.

The handoff includes run/build commands, route/component map, tokens, fixture descriptions, API types, integration examples, and a list of any unresolved server dependencies. It does not include deployment or infrastructure changes.
