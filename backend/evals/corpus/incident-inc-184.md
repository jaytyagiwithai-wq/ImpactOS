# Incident INC-184: payment reconciliation mismatch

## Summary

On 2026-02-14, invoice reconciliation failed for a subset of payment events
after an identifier mapping deployment. The billing adapter could not locate
the payer account when the expected customer correlation value was missing.

## Prevention

Contract changes must be tested with billing replay events. Event-field
retirements require consumer compatibility checks before release.
