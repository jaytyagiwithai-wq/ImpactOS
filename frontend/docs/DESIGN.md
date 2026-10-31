# ImpactOS visual direction

The public site and demo use black and gray surfaces, white type, and orange actions. The layout relies on readable headings, actual file excerpts, and a small number of functional controls.

The homepage opens with an upright API diff beside selectable findings and their source excerpts. It uses a responsive grid without rotated cards, fixed diagram coordinates, or floating captions. Selecting a finding updates its source header and excerpt together.

The document update example shows incoming files beside the complete set currently used for answers. It plays when requested, prepares files in sequence, and switches the active version and all listed source versions together. A failure leaves the existing version active.

Decorative category labels, uppercase microcopy, fictional company names, redundant comparison content, and tilted document artwork were removed. File names, version numbers, status, and source locations remain because they help visitors inspect the example.

The app keeps one flow: choose a change, open its report, and inspect sources. No dashboard or management tables are part of that flow.

Current public components live in src/components/product-demos.tsx and src/components/landing.tsx. Their styling is in src/app/product-demos.css and src/app/public-dark.css. See APP_DESIGN.md for the app.

## Connected hero composition

Restored the change card, central brand mark, and three findings as a connected visual. Curved SVG paths are measured from the rendered card bounds with ResizeObserver, rather than fixed scene coordinates. A small moving trace follows the selected route. Selecting a finding updates the linked source; the source opens in a dialog.

Cards remain upright, and the page keeps its plain copy without decorative uppercase labels or fictional company names. The layout stacks on phones with routes in a side gutter. Motion has a pause/resume control, stops offscreen, and respects reduced-motion preferences.
