"""Enterprise Agentic Semantic Layer (EASL) Command Line Interface.

Unified CLI for:
- Querying governed enterprise data products with zero SQL injection
- Neurosymbolic Autonomous Query Reasoning (AQR) over RDF/OWL knowledge graphs
- Serving the enterprise REST API with OpenAPI documentation
- Validating semantic models, SHACL shapes, and data product contracts
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path


def _get_root() -> Path:
    return Path(__file__).resolve().parents[2]


def cmd_query(args: argparse.Namespace) -> int:
    """Execute a governed enterprise query through the deterministic semantic layer."""
    from semantic_layer.agents import AgentWorkflow
    from semantic_layer.models import CallerContext

    context = CallerContext(
        role=args.role,
        country=args.country,
    )
    workflow = AgentWorkflow()
    answer = workflow.answer(args.question, context)
    rendered = answer.to_dict()

    if args.json:
        print(json.dumps(rendered, indent=2, sort_keys=True, default=str))
        return 0

    print("=" * 80)
    print("EASL GOVERNED QUERY RESULT")
    print("=" * 80)
    print(f"Question:    {rendered['question']}")
    print(f"Root Entity: {rendered['plan']['root_entity']}")
    print(f"Products:    {', '.join(rendered['data_products'])}")
    print(f"Quality:     {rendered['quality']['status']} (Score: {rendered['quality']['score']})")
    print("-" * 80)
    print("COMPILED SQL:")
    print(rendered["compiled_query"]["sql"].strip())
    print("-" * 80)
    print("RESULT ROWS:")
    rows = rendered["result"]
    if not rows:
        print("  (0 rows returned)")
    else:
        for idx, row in enumerate(rows, 1):
            print(f"  [{idx}] {json.dumps(row, default=str)}")
    print("-" * 80)
    print(f"Provenance Digest: {rendered['provenance']['result_digest']}")
    print("=" * 80)
    return 0


def cmd_ask(args: argparse.Namespace) -> int:
    """Execute neurosymbolic Autonomous Query Reasoning over the RDF/OWL knowledge graph."""
    from semantic_layer.kg.loader import SAPKnowledgeGraph
    from semantic_layer.reasoning.reflective_agent import AQRReflectiveAgent

    root = _get_root()
    kg = SAPKnowledgeGraph()
    kg.load_ontologies([
        str(root / "semantic/ontology/sap_ppms.ttl"),
        str(root / "semantic/ontology/sap_support.ttl"),
        str(root / "semantic/data/sap_support_graph.ttl"),
    ])
    agent = AQRReflectiveAgent(kg)
    res = agent.run(args.question)

    if args.json:
        payload = {
            "question": args.question,
            "status": res.status.name,
            "reason_code": res.reason_code.name,
            "attempts": res.attempts,
            "sparql": res.sparql_final,
            "notes": res.predicted_note_numbers,
            "answer": res.answer,
            "bindings": res.bindings,
        }
        print(json.dumps(payload, indent=2, sort_keys=True, default=str))
        return 0

    print("=" * 80)
    print("EASL KNOWLEDGE GRAPH AQR REASONING")
    print("=" * 80)
    print(f"Question:        {args.question}")
    print(f"Status:          {res.status.name} ({res.reason_code.name})")
    print(f"Attempts:        {res.attempts}")
    if res.sparql_final:
        print("-" * 80)
        print("GENERATED SPARQL 1.1:")
        print(res.sparql_final.strip())
    print("-" * 80)
    print("ANSWER:")
    if res.answer:
        print(f"  {res.answer}")
    elif res.predicted_note_numbers:
        print(f"  Notes: {', '.join(res.predicted_note_numbers)}")
    elif res.bindings:
        for b in res.bindings:
            print(f"  • {b}")
    else:
        print("  (No answers found or abstained)")
    print("=" * 80)
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    """Launch the FastAPI REST API service."""
    import uvicorn

    print(f"Starting EASL REST API on {args.host}:{args.port}...")
    uvicorn.run("semantic_layer.api:app", host=args.host, port=args.port, reload=args.reload)
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate semantic models, vocabulary, SHACL shapes, and data product contracts."""
    from semantic_layer.validation import main as run_validation

    print("Validating semantic layer contracts and SHACL constraints...")
    return run_validation(["--assets-only"] if args.assets_only else [])


def cmd_info(args: argparse.Namespace) -> int:
    """Display information about registered data products, metrics, and vocabulary."""
    from semantic_layer.registry import SemanticRegistry

    registry = SemanticRegistry.from_repository(_get_root())
    products = registry.products
    metrics = registry.metrics
    concepts = registry.concepts

    print("=" * 80)
    print("ENTERPRISE AGENTIC SEMANTIC LAYER (EASL) - REGISTRY INFO")
    print("=" * 80)
    print(f"Registered Data Products ({len(products)}):")
    for name, p in sorted(products.items()):
        print(f"  • {name:<25} [Grain: {p.grain}, Classification: {p.classification}]")

    print(f"\nRegistered Metrics ({len(metrics)}):")
    for name, m in sorted(metrics.items()):
        print(f"  • {name:<25} [Formula: {getattr(m, 'formula', 'N/A')}]")

    print(f"\nCanonical Concepts ({len(concepts)}):")
    for name in sorted(concepts.keys())[:15]:
        print(f"  • {name}")
    if len(concepts) > 15:
        print(f"  ... and {len(concepts) - 15} more concepts")
    print("=" * 80)
    return 0


def cmd_demo(args: argparse.Namespace) -> int:
    """Run interactive demonstration workflows."""
    if args.mode in ("erp", "all"):
        from semantic_layer.demo import main as run_erp_demo

        print("\n=== RUNNING ERP SEMANTIC LAYER DEMO ===\n")
        run_erp_demo()
    if args.mode in ("aqr", "all"):
        from semantic_layer.demo_sap import run_demo as run_aqr_demo

        print("\n=== RUNNING KNOWLEDGE GRAPH AQR DEMO ===\n")
        run_aqr_demo()
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the EASL CLI."""
    parser = argparse.ArgumentParser(
        prog="easl",
        description="Enterprise Agentic Semantic Layer (EASL) - Zero-Trust Semantic Layer for AI Agents",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # query
    p_query = subparsers.add_parser("query", help="Query enterprise data products using natural language")
    p_query.add_argument("question", help="Natural language business question")
    p_query.add_argument("--role", default="FinancialControllerFR", help="Caller role (default: FinancialControllerFR)")
    p_query.add_argument("--country", default="FR", help="Caller country context (default: FR)")
    p_query.add_argument("--json", action="store_true", help="Output raw JSON response")
    p_query.set_defaults(func=cmd_query)

    # ask
    p_ask = subparsers.add_parser("ask", help="Ask knowledge graph questions via Autonomous Query Reasoning (AQR)")
    p_ask.add_argument("question", help="Natural language diagnostic/graph question")
    p_ask.add_argument("--json", action="store_true", help="Output raw JSON response")
    p_ask.set_defaults(func=cmd_ask)

    # serve
    p_serve = subparsers.add_parser("serve", help="Start the FastAPI REST server")
    p_serve.add_argument("--host", default="0.0.0.0", help="Bind host (default: 0.0.0.0)")
    p_serve.add_argument("--port", type=int, default=8000, help="Bind port (default: 8000)")
    p_serve.add_argument("--reload", action="store_true", help="Enable auto-reload for development")
    p_serve.set_defaults(func=cmd_serve)

    # validate
    p_validate = subparsers.add_parser("validate", help="Validate semantic assets and constraints")
    p_validate.add_argument("--assets-only", action="store_true", help="Run only asset validation")
    p_validate.set_defaults(func=cmd_validate)

    # info
    p_info = subparsers.add_parser("info", help="Inspect registered data products and metrics")
    p_info.set_defaults(func=cmd_info)

    # demo
    p_demo = subparsers.add_parser("demo", help="Run interactive demonstration")
    p_demo.add_argument("--mode", choices=["erp", "aqr", "all"], default="all", help="Demo mode to run")
    p_demo.set_defaults(func=cmd_demo)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
