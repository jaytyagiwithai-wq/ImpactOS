export const articles = [
  {
    slug: "evidence-before-confidence",
    category: "DESIGNING FOR TRUST",
    title: "Checking an answer against its sources.",
    excerpt:
      "An answer can sound certain and still be hard to inspect. The useful question is what supports each claim.",
    reading: "4 min read",
    art: "evidence",
    sections: [
      {
        heading: "Make the claim inspectable.",
        body: "In a change investigation, a finding should connect to something a reviewer can open: a specific code fragment, a versioned document, or an explicit relationship record. “Billing might break” is difficult to evaluate. “This handler directly reads the removed field” gives the reviewer a starting point.",
      },
      {
        heading: "Name what the evidence establishes.",
        body: "A line of code that reads a field establishes a dependency in that source version. It does not, by itself, prove that removing the field will cause a production outage. A compatibility layer, a different event version, or an unused execution path could change the consequence. The report should keep those distinctions visible.",
      },
      {
        heading: "Let a source be a source.",
        body: "The evidence viewer should preserve the source text and location. Summaries can help explain relevance, but should not replace the underlying excerpt. Code should read like code. A customer agreement should read like a document. Both should retain the version used by the investigation.",
      },
      {
        heading: "Make uncertainty useful.",
        body: "An unknown is most useful when it identifies the missing evidence and a reasonable next step. If the analytics handler is absent, say so and ask for that source. The absence of a finding is not a guarantee that the release is safe.",
      },
    ],
    quote:
      "A finding is a starting point for judgment. Its evidence should be within reach.",
  },
  {
    slug: "a-snapshot-is-a-promise",
    category: "SYSTEMS & CONTEXT",
    title: "Keeping document versions together.",
    excerpt:
      "Your sources keep changing. An investigation still needs a coherent picture of the versions it used.",
    reading: "3 min read",
    art: "version",
    sections: [
      {
        heading: "Give the report a stable context.",
        body: "A change report may draw from an API specification, several handlers, an integration manifest, and a customer document. Recording their specific versions makes it possible to explain what was available when the report was generated. The report should retain that context even after new versions arrive.",
      },
      {
        heading: "Stage the next version separately.",
        body: "Indexing a replacement document can take time. One implementation approach is to write the replacement generation separately, then switch the active version after the required work completes. A failed replacement can leave the previous completed version available.",
      },
      {
        heading: "Distinguish active from historical.",
        body: "Ordinary search can default to current active sources. A before-and-after investigation explicitly needs a baseline and a proposed version. The interface should show which context the user selected and avoid quietly mixing source versions across the two.",
      },
      {
        heading: "Preserve identity, recheck access.",
        body: "An immutable source reference helps make a report reproducible. It does not grant permanent access. If a reviewer’s permissions change or a source is removed, the system should still apply its current access rules when the source is requested.",
      },
    ],
    quote:
      "A stable reference explains where the evidence came from. Access rules still decide who can open it.",
  },
  {
    slug: "a-dependency-is-not-an-outage",
    category: "CHANGE INVESTIGATION",
    title: "A dependency is not an outage.",
    excerpt:
      "Tracing a relationship and predicting a failure are different claims. A useful investigation keeps them separate.",
    reading: "3 min read",
    art: "graph",
    sections: [
      {
        heading: "Follow the relationship.",
        body: "An API schema identifies the proposed edit. A consumer implementation may show how a field is read. A manifest may connect that consumer to a customer integration. These are different pieces of evidence that can form a traceable path.",
      },
      {
        heading: "Investigate the consequence.",
        body: "The downstream consequence can depend on compatibility behavior, traffic, deployment order, and customer migration arrangements. A documented relationship provides a reason to inspect those details. It does not eliminate the need for testing or review.",
      },
      {
        heading: "Use classifications with care.",
        body: "ImpactOS separates confirmed dependencies, possible impacts, and unknowns in its sample reports. These labels describe the support available for a claim. They are not numerical probabilities and should not be interpreted as automatic release approvals.",
      },
    ],
    quote:
      "The path explains why something deserves attention. The review determines what happens next.",
  },
] as const;
