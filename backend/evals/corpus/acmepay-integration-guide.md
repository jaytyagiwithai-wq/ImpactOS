# AcmePay integration guide

## payment.completed consumption

AcmePay receives `payment.completed` webhooks and stores `customer_id` as its
external customer correlation key. Its integration must migrate to
`account_reference` before the legacy field is removed.

AcmePay is an enterprise customer. Breaking webhook changes require a migration
guide and advance notice under the enterprise API change policy.
