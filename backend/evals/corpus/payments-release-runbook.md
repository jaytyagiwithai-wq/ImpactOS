# Payments release runbook

## Purpose and scope

This runbook is used by the Payments release owner for planned changes to the
payment event platform. It applies to code releases, configuration releases,
schema migrations, webhook contract changes, and operational rollouts. The
release owner is responsible for collecting evidence, recording decisions, and
stopping a release if a prerequisite is incomplete. A successful deployment is
not by itself proof that a change is safe for downstream users.

The runbook has separate sections so that operational readiness, customer
communication, consumer compatibility, and post-release verification are not
accidentally treated as the same activity. Teams should link the release
record to the source snapshot, pull request, migration plan, and incident
review when those artifacts exist.

## Standard deployment preparation

Before a normal application release, confirm the deployed build is traceable
to a reviewed commit and a reproducible artifact. Verify the environment,
feature-flag state, database migration order, rollback owner, and on-call
coverage. Confirm that dashboards cover request error rate, queue lag, payment
authorization failures, and webhook delivery success. These checks reduce
operational risk, but they do not prove compatibility with external webhook
consumers.

For configuration-only changes, document the previous value, the new value,
and the expected observable effect. Use a staged rollout where practical.
Watch the change for the agreed observation window before increasing traffic.
If a metric regresses, pause the rollout and use the documented rollback path.

## Data migration preparation

For database changes, identify read paths, write paths, backfill work, and
recovery steps. Expand database schemas before writing new values. Keep old
read paths working while data is being migrated. A migration must be restartable
and must expose a measurable completion condition. Do not couple a large
backfill with an irreversible application deploy unless the team has rehearsed
the recovery procedure.

Database migrations are evaluated separately from event-contract changes.
A completed database migration cannot be used as evidence that an API consumer
has migrated. The release owner records these as distinct readiness items.

## Webhook contract retirement

This section applies when a field, event, endpoint, or required behavior is
removed from a payment webhook. Before removing `customer_id`, the release
owner must verify that the **Billing Adapter** has migrated to
`account_reference` and has passed replay validation with representative
payment events. The owner must also confirm the externally consumed contract
has a versioned compatibility path and that affected customers received **30
days written notice** with a migration guide.

The verification record must name every known consumer, the responsible owner,
the result of replay testing, and the date notice was sent. A consumer with an
unknown owner is not automatically safe; it remains an open risk. If any known
consumer cannot accept the replacement field, retain the compatible payload or
delay retirement. The release reviewer should reject a change that only proves
the producer deployed successfully while consumer migration remains unknown.

## Incident and rollback readiness

For releases that affect payment processing, review the prior incidents most
similar to the proposed failure mode. Confirm the alert route, escalation
contact, and rollback authority. Prepare a dashboard view that shows webhook
delivery failures, payment reconciliation errors, and a count of events that
cannot be associated with an account. The on-call engineer should be able to
disable the new path without waiting for a new build when a feature flag is
available.

During an active incident, prioritize stabilizing payment processing. Do not
attempt a broad contract cleanup at the same time as an emergency rollback.
Capture affected event identifiers and preserve the release timeline for the
follow-up investigation.

## Post-release observation

After deployment, compare webhook delivery, payment reconciliation, and
consumer error rates with the pre-release baseline. Observe the release long
enough to cover ordinary traffic variation. Check both aggregate service health
and the named consumers identified during planning. A green API error-rate
graph does not rule out a downstream integration failure.

Close the release only after the owner records the observed outcome, links
supporting dashboards, and resolves or explicitly accepts any remaining risks.
If a compatibility check was deferred, open a tracked follow-up with a named
owner and due date rather than silently treating it as complete.

## Routine operational notes

The Payments team uses a standard change window for non-urgent releases. The
window improves coordination with support and on-call staff but does not waive
technical or contractual readiness requirements. Keep deployment messages
short, include the release identifier, and state whether a rollback is safe.

For a routine dependency upgrade that does not change an API or event contract,
use the standard deployment preparation and post-release observation sections.
Do not create customer notices merely because an internal library version has
changed. Conversely, do not classify a public event-field removal as routine
maintenance simply because the application deployment itself is small.
