# Billing adapter consumer

## Webhook dependency

The billing adapter handles `payment.completed` events. Its reconciliation
handler reads `customer_id` to find the payer account before creating an
invoice record.

Removing `customer_id` without a compatible replacement can break invoice
reconciliation. The billing adapter must accept `account_reference` before the
old field is retired.

Owner: Billing Platform
Dependency type: runtime event consumer
