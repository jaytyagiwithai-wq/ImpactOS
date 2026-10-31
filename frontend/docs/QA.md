# Frontend checks — 28 October 2026

## Simplified demo revision

- Production build and TypeScript: passed after the simplified layout and shadcn integration.
- Desktop visual checks: dark homepage, sample composer, report, and source drawer.
- Mobile visual checks: 390px homepage, sample composer, report, and source library.
- Sample selection: choosing the retry case changes the diff, question, versions, and report together.
- Question editing: custom text disables the prepared-report action and explains that live analysis is unavailable; restoring the sample question re-enables it.
- Keyboard: Arrow Down and Enter move between and expand report findings. Escape closes the source drawer. Focus returns to its opening button.
- Source provenance: finding links open the expected excerpt, version, and location. The drawer's all-sources list works without a separate management table.
- Export: the actual report export action was checked for all three samples, including report title, baseline/proposed versions, findings, next steps, source names and locations, filename, and download action.
- Old dashboard and management routes redirect to the simplified demo; direct sample report URLs remain supported.

All workspace data is synthetic. No live backend, authentication, AI inference, upload, indexing, deployment, or automated screen-reader audit was tested. There is no configured lint script in this project.

## Color and version-animation revision

The public site and app now use neutral grayscale surfaces and text. The orange action color is #ff5c35; green, amber, and red are reserved for status and diffs.

The version demo now has explicit preparation, indexing, activation, and final states. It runs when visible, stops at the final result, and supports replay and success/failure selection. Mobile uses vertical connectors with visible moving markers. Successful updates show payments-v3 active; failed updates preserve payments-v2. The shared pause control pauses the timers and CSS motion, and reduced-motion preferences show the completed state without playback.

Desktop and 390px mobile layouts were inspected, and both update outcomes were checked in the browser. The production build passed after this revision.

## Logo revision

Replaced the radial star with a custom solid split-path mark. The shared Mark component updates navigation, hero decoration, diagram hub, and footer. Added a standalone SVG and matching browser icon. The homepage was visually checked, and the production build passed with the new icon route.

## Layout and copy cleanup

The homepage now uses ChangePreview and VersionDemo from src/components/product-demos.tsx. Styles are in src/app/product-demos.css. The old floating-node and three-column version scenes are removed from the rendered page.

Decorative uppercase labels and fictional company branding are removed from the homepage, app, notes, and source fixtures. Functional metadata such as source paths and versions remains. Document artwork is upright, and the duplicate comparison section is removed.

Browser checks covered 1440px and 854px desktop layouts plus a 390px phone layout. Selecting a finding opens the matching source excerpt. Successful updates prepare all three files before changing the answer context to v3. Failed updates keep the answer context at v2. Report exports still pass for all three cases after the source-name changes.

## Connected composition revision

Checked the restored connected preview at 854px, 1440px, and 390px. Card edges and curved paths stay aligned after resizing and mobile stacking. Finding selection updates the source link, the source dialog opens the selected file, and pause/resume controls toggle the trace animation. Source line numbers now recognize locations such as Section 4.2, lines 12–14.
