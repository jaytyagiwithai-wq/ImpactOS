"""Consumer for payment.completed events in the billing adapter.

The v3 webhook migration must not remove customer_id until all consumers use
account_reference. This handler is a deliberately realistic source in the
ImpactOS demo corpus: it represents code evidence, not a policy document.
"""

from dataclasses import dataclass


class RetryableConsumerError(Exception):
    """The event can be retried after the producer contract is restored."""


@dataclass(frozen=True)
class PaymentCompleted:
    payment_id: str
    customer_id: str
    amount: int


def handle_payment_completed(event: dict, account_repository, ledger) -> None:
    # customer_id is required by the current v2/v3 compatibility path.
    customer_id = event.get("customer_id")
    if not customer_id:
        raise RetryableConsumerError(
            "payment.completed requires customer_id until account_reference "
            "is rolled out to all billing consumers"
        )

    account = account_repository.find_by_legacy_customer_id(customer_id)
    if account is None:
        raise RetryableConsumerError("No billing account for customer_id")

    ledger.record_payment(
        account_id=account.id,
        payment_id=event["payment_id"],
        amount=event["amount"],
    )
