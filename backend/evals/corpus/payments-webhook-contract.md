# Payments webhook contract

## payment.completed v3

The `payment.completed` webhook currently includes `customer_id` for existing
integrations. New consumers should prefer `account_reference`.

Removing `customer_id` is a breaking change. Create a versioned webhook
contract, keep a backward-compatible payload during migration, and verify all
known consumers before retirement.

## Release requirements

Before the field is removed, the release owner must confirm consumer migration,
publish an API migration guide, and obtain the required customer notice.
