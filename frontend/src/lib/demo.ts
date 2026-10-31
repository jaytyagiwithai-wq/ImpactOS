export type Source = {
  id: string;
  name: string;
  kind: "Code" | "OpenAPI" | "Document" | "Manifest" | "Incident";
  version: string;
  location: string;
  lines: string[];
  highlight?: number;
  note: string;
};
export const sources: Source[] = [
  {
    id: "billing",
    name: "billing/handlers.py",
    kind: "Code",
    version: "b7c21ad",
    location: "Lines 84–88",
    lines: [
      "def on_payment_completed(event):",
      "    account = find_account(",
      '        event["customer_id"]',
      "    )",
      "    account.record_payment(event)",
    ],
    highlight: 2,
    note: "The handler directly reads customer_id. This establishes a code dependency; the actual failure behavior still needs testing.",
  },
  {
    id: "contract",
    name: "customers/service-agreement.md",
    kind: "Document",
    version: "v2",
    location: "Section 4.2 · lines 12–14",
    lines: [
      "Breaking integration changes require",
      "30 days of advance written notice.",
      "Scope is reviewed with the customer.",
    ],
    highlight: 1,
    note: "This fictional agreement contains a notice provision. Whether it applies to the proposed change requires human review.",
  },
  {
    id: "manifest",
    name: "integrations/customer.yaml",
    kind: "Manifest",
    version: "v1",
    location: "Lines 1–4",
    lines: [
      "customer: example",
      "adapter: billing",
      "event: payment.completed",
      "owner: integrations-team",
    ],
    highlight: 1,
    note: "The explicit manifest connects the fictional customer to the billing adapter.",
  },
  {
    id: "schema",
    name: "webhooks/payment.yaml",
    kind: "OpenAPI",
    version: "v2 → v3",
    location: "#/components/schemas/PaymentEvent",
    lines: [
      "payment.completed:",
      "  payment_id: string",
      "- customer_id: string",
      "  amount: integer",
    ],
    highlight: 2,
    note: "The proposed schema removes customer_id. This is a synthetic diff excerpt, not a full OpenAPI document.",
  },
  {
    id: "retry",
    name: "payments/retry_policy.py",
    kind: "Code",
    version: "a6d31ce",
    location: "Lines 20–24",
    lines: [
      "def retry_payment(attempt):",
      "    if attempt < MAX_RETRIES:",
      "        queue.retry_after(30)",
      "    else:",
      "        dead_letter_queue.send(attempt)",
    ],
    highlight: 1,
    note: "The consumer uses a configured retry limit. Changing that limit may change when failures reach the dead-letter queue.",
  },
  {
    id: "incident",
    name: "incidents/INC-008.md",
    kind: "Incident",
    version: "v1",
    location: "Mitigation notes",
    lines: [
      "A delayed retry obscured delivery failures.",
      "The team added a dead-letter alert.",
      "Follow-up: verify retry policy changes.",
    ],
    highlight: 2,
    note: "A historical incident suggests a useful verification step. It does not establish that another incident will happen.",
  },
  {
    id: "catalog",
    name: "services/catalog.yaml",
    kind: "Manifest",
    version: "v4",
    location: "Analytics service entry",
    lines: [
      "service: analytics",
      "subscribes_to: payment.completed",
      "owner: data-platform",
      "handler_source: not_in_snapshot",
    ],
    highlight: 3,
    note: "The catalog names a subscriber but does not show whether that consumer reads the removed field.",
  },
];
export type Finding = {
  id: string;
  title: string;
  entity: string;
  kind: "confirmed" | "possible" | "unknown";
  description: string;
  sourceIds: string[];
  next: string;
};
export type Investigation = {
  id: string;
  title: string;
  short: string;
  project: string;
  status: "Ready" | "Needs review";
  baseline: string;
  proposed: string;
  date: string;
  field: string;
  question: string;
  findings: Finding[];
};
export const investigations: Investigation[] = [
  {
    id: "INV-014",
    title: "Remove customer_id from the payment webhook",
    short: "Payment webhook · remove customer_id",
    project: "Payments API",
    status: "Needs review",
    baseline: "payments-v2",
    proposed: "payments-v3",
    date: "28 Oct 2026",
    field: "customer_id",
    question:
      "Which consumers and customer commitments need review before we remove this field?",
    findings: [
      {
        id: "F-01",
        title: "Billing adapter reads the removed field",
        entity: "Billing adapter",
        kind: "confirmed",
        description:
          "The payment handler directly indexes customer_id to look up a billing account. The consumer needs a compatibility review before this field is removed.",
        sourceIds: ["billing", "schema"],
        next: "Update the account lookup and test the handler against both event versions.",
      },
      {
        id: "F-02",
        title: "Customer integration’s migration notice needs review",
        entity: "Customer integration",
        kind: "possible",
        description:
          "An integration manifest connects Customer integration to this adapter. The fictional agreement contains an advance-notice provision for breaking changes.",
        sourceIds: ["manifest", "contract"],
        next: "Ask the integration owner whether the notice provision applies and agree a migration window.",
      },
      {
        id: "F-03",
        title: "Analytics consumer remains unverified",
        entity: "Analytics",
        kind: "unknown",
        description:
          "The service catalog names an analytics subscriber, but the handler source is missing. This snapshot cannot establish whether it reads customer_id.",
        sourceIds: ["catalog"],
        next: "Add the consumer source to a new snapshot and repeat the investigation.",
      },
    ],
  },
  {
    id: "INV-013",
    title: "Increase the payment retry limit",
    short: "Payment delivery · adjust retry limit",
    project: "Payments API",
    status: "Ready",
    baseline: "delivery-v1",
    proposed: "delivery-v2",
    date: "27 Oct 2026",
    field: "MAX_RETRIES",
    question: "What needs verification if the payment retry limit increases?",
    findings: [
      {
        id: "F-11",
        title: "Retry policy uses the configured limit",
        entity: "Payment delivery",
        kind: "confirmed",
        description:
          "The handler compares the current attempt with MAX_RETRIES before choosing a retry or the dead-letter queue.",
        sourceIds: ["retry"],
        next: "Test both retry and dead-letter paths using the proposed limit.",
      },
      {
        id: "F-12",
        title: "Verify delivery-failure alert timing",
        entity: "Delivery operations",
        kind: "possible",
        description:
          "A fictional historical incident notes that delayed retries obscured delivery failures. The proposed limit merits an alert-timing review.",
        sourceIds: ["incident"],
        next: "Check that the dead-letter alert remains useful at the proposed retry limit.",
      },
    ],
  },
  {
    id: "INV-012",
    title: "Document the analytics subscriber",
    short: "Service catalog · document a subscriber",
    project: "Service catalog",
    status: "Ready",
    baseline: "catalog-v3",
    proposed: "catalog-v4",
    date: "26 Oct 2026",
    field: "analytics",
    question:
      "Does the catalog establish the analytics consumer’s field dependencies?",
    findings: [
      {
        id: "F-21",
        title: "Subscriber is listed in the catalog",
        entity: "Analytics",
        kind: "confirmed",
        description:
          "The catalog records that analytics subscribes to payment.completed. It does not enumerate the fields consumed by its handler.",
        sourceIds: ["catalog"],
        next: "Link the concrete handler implementation to the service record.",
      },
      {
        id: "F-22",
        title: "Field-level dependency evidence is missing",
        entity: "Analytics",
        kind: "unknown",
        description:
          "No consumer handler is present in this snapshot, so field-level impact cannot be confirmed.",
        sourceIds: ["catalog"],
        next: "Include the handler source before evaluating a field removal.",
      },
    ],
  },
];
export const kindLabels = {
  confirmed: "Confirmed dependency",
  possible: "Possible impact",
  unknown: "Unknown",
};
export const getInvestigation = (id: string) =>
  investigations.find((i) => i.id === id);
export const getSource = (id: string) => sources.find((s) => s.id === id);
