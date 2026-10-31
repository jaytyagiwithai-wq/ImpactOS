# ImpactOS frontend

A small, dark demo for the ImpactOS change-impact project. The homepage explains the idea; the app lets a visitor choose a sample change, open its report, and inspect the source excerpts.

## Run

```powershell
npm ci
npm run dev
```

Open http://127.0.0.1:4178. Both development and production use port 4178, so run one server at a time.

```powershell
npm run typecheck
npm run build
npm run start
```

## The demo flow

1. Open `/app` and choose one of three sample changes.
2. Read the change excerpt and sample question.
3. Open its prepared report.
4. Expand a finding and click a source to inspect its version and excerpt.

The Sources button opens a simple file list in a drawer. Reports can be exported as Markdown. Custom questions clearly show that live analysis is not connected. There is no fake progress animation or simulated AI result.

The previous dashboard, sidebar, tables, and settings are no longer in the app flow. Their implementation is preserved locally under ignored `work/legacy-workspace-v1/`. Old routes redirect to `/app`. Existing report URLs still work, such as `/app/investigations/INV-014`.

## Components and styling

- shadcn/ui components are owned source files in `src/components/ui/`.
- The demo uses Button, Textarea, Accordion, and Sheet, with Radix primitives for keyboard and focus behavior.
- `components.json` configures the registry; `postcss.config.mjs` enables Tailwind CSS 4.
- `src/app/shadcn.css` defines the component theme.
- `src/app/app/demo.css` styles the simplified app.
- `src/app/public-dark.css` gives the editorial homepage and public pages their dark palette.
- Fonts are local in `public/fonts/`, with licenses.
- The custom split-path logo is in `public/impactos-mark.svg`; see `docs/BRAND.md` for its shared component and favicon.

See `docs/THIRD_PARTY.md` for the shadcn/ui notice.

## Backend handoff

All records are synthetic. There is no live authentication, document upload, indexing, inference, authorization, or persistence in this frontend.

The typed HTTP boundary remains in `src/lib/api.ts`, with contracts in `src/contracts/impactos.ts`. The current UI reads `src/lib/demo.ts`. Replace that fixture mapping and the sample-report action in `src/components/demo-workspace.tsx` when the FastAPI endpoints are ready.

`NEXT_PUBLIC_DATA_MODE=api` shows a connection state until integration is completed. It never silently falls back to the sample reports. Keep credentials and backend enforcement on the server. See `docs/INTEGRATION_CONTRACT.md` for the proposed API contract.

Both user-supplied reference repositories remain untouched. Historical plans and concepts describe earlier versions; this README and `docs/APP_DESIGN.md` describe the current app.

The homepage demos are implemented in src/components/product-demos.tsx with src/app/product-demos.css. They use aligned panels and on-request update playback. Decorative uppercase labels and fictional company names have been removed from the current UI.
