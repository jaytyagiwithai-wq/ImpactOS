# Analytics consumer inventory

The analytics event pipeline consumes `payment.completed` but uses `payment_id`
and `merchant_id` for aggregation. The current inventory contains no verified
runtime read of `customer_id`.

This is an evidence gap, not proof that the field is safe to remove. The
analytics owner should confirm the current production handler before release.
