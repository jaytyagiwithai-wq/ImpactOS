# Proposed frontend/backend contract

Draft for coordination, not a claim that these endpoints exist. Jayat owns implementation and final server semantics. The frontend should adapt through one typed client if endpoint names differ.

## Transport and session

Use an environment-configured HTTPS API origin. Choose one session approach together before real integration: same-site HttpOnly cookie session, or the chosen OIDC provider's supported browser flow. Do not invent a token storage strategy in the UI. Cookie-based cross-origin requests require compatible CORS, cookie attributes, and CSRF protection on the server. No long-lived service credentials in NEXT_PUBLIC variables.

Every API action derives authority from the verified session. Organization/project IDs are context, not proof of access. Clear data caches on sign-out or organization changes. The frontend may hide unavailable controls but must handle 401/403 from every endpoint.

## Candidate endpoints

| Endpoint | Frontend need |
|---|---|
| GET /v1/me | Session identity, memberships, allowed actions |
| GET /v1/projects | Authorized projects |
| GET /v1/projects/{id}/snapshots | Available immutable baseline snapshots |
| GET /v1/investigations?project_id=&status=&q=&cursor= | Paginated list |
| POST /v1/investigations | Submit a validated change input; return job ID and queued status |
| GET /v1/investigations/{id} | Job state, stage, updated time, report when ready |
| POST /v1/investigations/{id}/cancel | Only if cancellation is supported; otherwise omit control |
| GET /v1/documents?project_id=&cursor= | Paginated source list |
| GET /v1/documents/{id}/versions | Authorized version history |
| POST /v1/uploads | Validate upload intent, return upload instructions and record ID |
| POST /v1/uploads/{id}/complete | Confirm upload and enqueue server-side indexing |
| GET /v1/jobs/{id} | Indexing state, safe error details, retry eligibility |
| POST /v1/jobs/{id}/retry | Authorized retry when supported |
| GET /v1/evidence/{id} | Authorized versioned source excerpt and location |
| GET /v1/dependencies?project_id=&snapshot_id=&entity_id=&depth= | Bounded authorized nodes/edges with provenance |

The server validates size/type/content and file ownership; client checks are convenience. Signed upload instructions are time-limited and scoped. Do not put private source contents into URLs, telemetry, or client-side persistent storage by default.

## Status semantics

Job state: queued, running, completed, failed, cancelled. A server-supplied stage may be parsing, retrieving, traversing, reranking, or generating. Only show stages the server actually reports. Unknown future stages fall back to a neutral “Processing” label rather than breaking rendering.

Report completeness is separate from job status: complete or partial. Finding classification is confirmed_dependency, possible_impact, or unknown. Optional severity is separate. No frontend-generated probabilities or final classifications.

Completed reports include the selected snapshot, change summary, findings, evidence IDs, dependency paths, unknowns, and suggested next steps. An empty findings list does not mean “safe to deploy”; show the report's coverage/limitations.

## Errors and polling

Standard safe error shape: `{ error: { code, message, request_id, field_errors? } }`. Handle 400/422 validation, 401 session expired, 403 forbidden, 404 unavailable resource, 409 conflicting/stale state, 413 file too large, 429 rate limited, and 5xx service unavailable. Respect Retry-After where supplied.

Poll active jobs with bounded backoff, cancel requests on navigation, pause when the tab is hidden where appropriate, and stop at terminal states. Do not retry mutations blindly; use server-supported idempotency keys for job creation. Show stale-state notices when updates stop. Never silently replace failed live data with demo fixtures.

## Evidence and graphs

Evidence contains immutable source version plus a typed location: code line range, page, or JSON pointer. The server authorizes every fetch and returns only accessible content. If permissions change, clear already displayed stale evidence after an authorization failure.

Nodes/edges are data to render, not conclusions to create. Each edge includes evidence IDs and snapshot context. The backend bounds graph expansion, filters permissions, and avoids leaking hidden node names/counts. The frontend offers an equivalent textual path.

## Frontend integration test cases

Session expired mid-investigation; forbidden citation; source removed; indexing failed; no relevant evidence; partial report; duplicate submit; network timeout; file too large; stale snapshot; empty workspace; rate limit; delayed job update; and a completed investigation with no affected entities.

Test the adapter with fixtures first, then the same journey against your service. Backend authorization and inference correctness remain backend test responsibilities, while the frontend verifies faithful state presentation and safe error handling.
