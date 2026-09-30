"""Enterprise Agentic Semantic Layer (EASL) - 30-Second Quickstart.

Demonstrates querying governed enterprise data products without SQL injection risk
and receiving a cryptographically verifiable provenance envelope.
"""

from __future__ import annotations

from semantic_layer.agents import AgentWorkflow
from semantic_layer.models import CallerContext


def main() -> None:
    print("=" * 70)
    print("EASL Python SDK Quickstart")
    print("=" * 70)

    # 1. Initialize the Governed Agent Workflow
    workflow = AgentWorkflow()

    # 2. Define the Caller Context (Role-Based Access & Policy Control)
    context = CallerContext(role="FinancialControllerFR", country="FR")

    # 3. Submit a Natural Language Business Question
    question = (
        "Find French automotive business partners with at least three qualifying financial postings "
        "in the last 12 months and total debit loss above EUR 20,000."
    )
    print(f"\n[1] Question: {question}")

    # 4. Execute Governed Reasoning & Query Planning
    print("\n[2] Executing Governed Semantic Resolution & Query Planning...")
    answer = workflow.answer(question, context)
    rendered = answer.to_dict()

    # 5. Inspect Results
    print(f"\n[3] Quality Check: {rendered['quality']['status']}")
    print(f"[4] Data Products Queried: {', '.join(rendered['data_products'])}")
    print("\n[5] Generated Parameterized SQL (Zero SQL-Injection):")
    print(rendered["compiled_query"]["sql"].strip())

    print("\n[6] Execution Results:")
    for row in rendered["result"]:
        print(f"    Partner ID: {row['partner_id']}, Total Debit Loss: EUR {row['total_debit_loss_eur']:,.2f}")

    print("\n[7] Cryptographic Provenance Digest:")
    print(f"    {rendered['provenance']['result_digest']}")
    print("\nDone! Full audit trail and data digests preserved.\n")


if __name__ == "__main__":
    main()
