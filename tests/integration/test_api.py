"""HTTP transport coverage for the deterministic semantic agent."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from semantic_layer.api.app import create_app

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PRIMARY_QUESTION = (
    "Find French motor-insurance customers with at least three qualifying claims "
    "in the last 12 months and total incurred loss above EUR 20,000."
)


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(REPOSITORY_ROOT, provenance_path=tmp_path / "provenance.sqlite"))


def test_execute_endpoint_returns_traceable_agent_answer(client: TestClient) -> None:
    """A successful execute response must include independently retrievable evidence."""

    response = client.post("/execute", json={"question": PRIMARY_QUESTION, "role": "ClaimsAnalystFR"})

    assert response.status_code == 200
    body = response.json()
    assert body["provenance"]["quality_status"] == "PASS"
    assert body["plan"]["root_entity"] == "insurance:Customer"
    assert "SELECT" in body["compiled_query"]["sql"]

    provenance = client.get(f"/provenance/{body['provenance']['query_id']}")
    assert provenance.status_code == 200
    assert provenance.json()["query_id"] == body["provenance"]["query_id"]


def test_public_catalog_and_request_endpoints_are_thin_governed_adapters(client: TestClient) -> None:
    """Removing a public transport route would break the documented API contract."""

    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/concepts").status_code == 200
    assert client.get("/metrics").status_code == 200
    assert client.get("/data-products").status_code == 200
    assert client.get("/mappings").status_code == 200
    assert client.post("/resolve", json={"question": PRIMARY_QUESTION}).json()["concept_ids"]
    assert client.post("/query-plan", json={"question": PRIMARY_QUESTION, "role": "ClaimsAnalystFR"}).status_code == 200
    assert client.post("/validate", json={}).json()["status"] == "PASS"


def test_api_documents_caller_role_as_simulation_not_authentication(client: TestClient) -> None:
    """The local transport must not imply that a user-supplied role is identity proof."""

    description = client.get("/openapi.json").json()["info"]["description"]
    assert "simulated" in description.lower()
    assert "authentication" in description.lower()


def test_execute_endpoint_does_not_execute_for_an_unknown_role(client: TestClient) -> None:
    """Changing a transport error into an execution response would bypass authorization."""

    response = client.post("/execute", json={"question": PRIMARY_QUESTION, "role": "UnknownRole"})

    assert response.status_code == 403
    assert "ROLE_DENIED" in response.json()["detail"]


def test_query_plan_endpoint_denies_unknown_role_before_final_plan(client: TestClient) -> None:
    """Moving pre-authorization out of this route would disclose a final plan to a denied caller."""

    response = client.post("/query-plan", json={"question": PRIMARY_QUESTION, "role": "UnknownRole"})

    assert response.status_code == 403
    assert "ROLE_DENIED" in response.json()["detail"]


def test_query_and_execute_endpoints_reject_residual_constraint_language(client: TestClient) -> None:
    question = PRIMARY_QUESTION + " for customer FR_001"

    query_plan = client.post("/query-plan", json={"question": question, "role": "ClaimsAnalystFR"})
    execute = client.post("/execute", json={"question": question, "role": "ClaimsAnalystFR"})

    assert query_plan.status_code == 422
    assert execute.status_code == 422
    assert "customer restrictions" in query_plan.json()["detail"]


@pytest.mark.parametrize(
    "question",
    [
        f"{PRIMARY_QUESTION};",
        f"{PRIMARY_QUESTION} -- comment",
        f"{PRIMARY_QUESTION} /* comment */",
        f"SELECT * FROM claims; {PRIMARY_QUESTION}",
        f"DROP TABLE claims; {PRIMARY_QUESTION}",
        f"INSERT INTO claims VALUES (1); {PRIMARY_QUESTION}",
        f"PRAGMA database_list; {PRIMARY_QUESTION}",
        f"ATTACH 'other.db' AS other; {PRIMARY_QUESTION}",
        f"VACUUM; {PRIMARY_QUESTION}",
    ],
)
def test_execute_rejects_sql_shaped_business_questions(client: TestClient, question: str) -> None:
    """Removing request-boundary validation would allow non-business syntax into the workflow."""

    response = client.post("/execute", json={"question": question, "role": "ClaimsAnalystFR"})

    assert response.status_code == 422
    assert "SQL-shaped" in response.text
