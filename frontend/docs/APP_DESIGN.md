# ImpactOS app design

The app is a focused demo for a portfolio review. It presents one path: select a change, read the findings, inspect the sources.

## Structure

A small top bar contains the logo, a demo label, Sources, and a link to the public site. There is no persistent sidebar, KPI dashboard, organization switcher, account menu, or management table.

The initial screen offers three prepared changes. A compact code excerpt, question, version pair, and one primary action form the main panel. Editing a question explains that live analysis is unavailable and offers a restore action.

The report shows its title, versions, and a short list of findings. A shadcn Accordion reveals one finding at a time. Source buttons open a shadcn Sheet with a readable excerpt, version, location, and note. The source library is a plain list instead of a table.

## Theme

Neutral black page surfaces, gray panels, bright white text, and saturated orange actions (#ff5c35). Color is reserved for actions, selected elements, and status. The homepage retains its editorial Instrument Serif headings and bespoke animated sections, now in the same dark palette. The app uses Geist for text and Plex Mono for code and identifiers.

Body text stays around 14–15px, with 17–18px question text, 13px controls, and smaller code metadata. Mobile rearranges the primary action and source drawer without adding navigation layers. Reduced-motion preferences are respected.

## Components

Owned shadcn/ui source: Button, Textarea, Accordion, Sheet (Radix). The registry configuration is `components.json`, and the theme is `src/app/shadcn.css`. The app's layout and spacing remain custom.

Main files:

- `src/components/demo-workspace.tsx`: sample selection, question, report, export
- `src/components/workspace-shell.tsx`: top bar and shared source-drawer state
- `src/components/source-drawer.tsx`: file list and source detail view
- `src/app/app/demo.css`: app styling
- `src/app/public-dark.css`: public dark theme

The previous dashboard implementation is archived in ignored `work/legacy-workspace-v1/` and is not shipped in the source package.

