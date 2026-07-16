from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from yarvis_api.main import app

client = TestClient(app)


def create_source_and_document():
    source = client.post(
        "/observations/sources",
        json={
            "source_type": "manual_import",
            "source_name": "Manual Intake",
            "received_at": datetime(2026, 7, 16, tzinfo=timezone.utc).isoformat(),
            "classification": "internal",
            "metadata": {"channel": "upload"},
        },
    )
    assert source.status_code == 201, source.text

    document = client.post(
        "/observations/documents",
        json={
            "source_id": source.json()["id"],
            "filename": "report.csv",
            "media_type": "text/csv",
            "file_content": "store_id,inactive_days\nS-1,65",
            "classification": "netpay",
            "metadata": {"processor": "pytest"},
        },
    )
    assert document.status_code == 201, document.text
    return source.json(), document.json()["document"]


def test_source_registration_and_document_hash_deduplication():
    source, document = create_source_and_document()

    duplicate = client.post(
        "/observations/documents",
        json={
            "source_id": source["id"],
            "filename": "same.csv",
            "media_type": "text/csv",
            "file_content": "store_id,inactive_days\nS-1,65",
        },
    )
    assert duplicate.status_code == 201
    assert duplicate.json()["created"] is False
    assert duplicate.json()["duplicate_by"] == "file_hash"
    assert duplicate.json()["document"]["id"] == document["id"]


def test_observation_create_confirm_reject_conflict_supersede_and_immutability():
    source, document = create_source_and_document()

    first = client.post(
        "/observations",
        json={
            "source_id": source["id"],
            "document_id": document["id"],
            "domain": "netpay",
            "subject_type": "store",
            "subject_reference": "S-1",
            "field_name": "inactive_days",
            "observed_value": {"value": 65},
            "normalized_value": {"value": 65},
            "identifier_type": "store_id",
            "extraction_method": "csv_parser",
            "confidence": 0.98,
            "confirmation_status": "candidate",
            "source_reference": "line:2",
            "provenance": {"processor": "pytest", "version": "1"},
        },
    )
    assert first.status_code == 201, first.text
    observation_id = first.json()["id"]

    confirmed = client.post(f"/observations/{observation_id}/confirm", json={"actor": "operator@local"})
    assert confirmed.status_code == 200
    assert confirmed.json()["confirmation_status"] == "confirmed"

    conflicted = client.post(f"/observations/{observation_id}/conflict", json={"actor": "operator@local"})
    assert conflicted.status_code == 200
    assert conflicted.json()["confirmation_status"] == "conflicted"

    replacement = client.post(
        "/observations",
        json={
            "source_id": source["id"],
            "document_id": document["id"],
            "domain": "netpay",
            "subject_type": "store",
            "subject_reference": "S-1",
            "field_name": "inactive_days",
            "observed_value": {"value": 66},
            "extraction_method": "csv_parser",
            "confidence": 0.97,
            "confirmation_status": "candidate",
        },
    )
    assert replacement.status_code == 201

    superseded = client.post(
        f"/observations/{observation_id}/supersede",
        json={"actor": "operator@local", "replacement_observation_id": replacement.json()["id"]},
    )
    assert superseded.status_code == 200
    assert superseded.json()["confirmation_status"] == "superseded"

    reject_after_terminal = client.post(f"/observations/{observation_id}/reject", json={"actor": "operator@local"})
    assert reject_after_terminal.status_code == 409


def test_resolution_proposal_and_confirmation():
    source, document = create_source_and_document()
    observation = client.post(
        "/observations",
        json={
            "source_id": source["id"],
            "document_id": document["id"],
            "domain": "netpay",
            "subject_type": "store",
            "subject_reference": "S-1",
            "field_name": "store_id",
            "observed_value": {"value": "S-1"},
            "extraction_method": "csv_parser",
            "confidence": 0.95,
            "confirmation_status": "candidate",
        },
    )
    assert observation.status_code == 201

    proposal = client.post(
        f"/observations/{observation.json()['id']}/resolution-proposals",
        json={
            "candidate_entity_type": "Store",
            "candidate_entity_id": "store-internal-1",
            "confidence": 0.9,
            "explanation": "Strong store id match",
        },
    )
    assert proposal.status_code == 201

    confirmed = client.post(f"/resolutions/{proposal.json()['id']}/confirm", json={"actor": "reviewer@local"})
    assert confirmed.status_code == 200
    assert confirmed.json()["decision_status"] == "confirmed"


def test_policy_validation_allows_known_operators_and_blocks_unknown():
    allowed = [
        "equals",
        "not_equals",
        "greater_than",
        "greater_than_or_equal",
        "less_than",
        "less_than_or_equal",
        "in",
        "not_in",
        "days_since_greater_than",
        "exists",
        "missing",
    ]
    for index, operator in enumerate(allowed, start=1):
        response = client.post(
            "/operational-policies",
            json={
                "policy_key": f"custom.allowed.{operator}",
                "domain": "netpay",
                "version": 1,
                "status": "draft",
                "description": "allowed operator",
                "severity": "warning",
                "requires_human_approval": True,
                "configuration": {"conditions": [{"field": f"f{index}", "operator": operator, "value": 1}]},
            },
        )
        assert response.status_code == 201, response.text

    blocked = client.post(
        "/operational-policies",
        json={
            "policy_key": "custom.blocked.eval",
            "domain": "netpay",
            "version": 1,
            "status": "draft",
            "description": "blocked",
            "severity": "warning",
            "requires_human_approval": True,
            "configuration": {"conditions": [{"field": "x", "operator": "eval", "value": "__import__('os').system('x')"}]},
        },
    )
    assert blocked.status_code == 422


def test_watch_churn_critical_asset_and_insufficient_data_policies_create_attention_items():
    evaluations_before = client.get("/policy-evaluations").json()

    watch = client.post(
        "/operational-policies/evaluate",
        json={
            "policy_key": "netpay.store.watch_inactivity",
            "subject_type": "store",
            "subject_id": "S-10",
            "facts": {"inactive_days": 30},
            "evidence_references": [{"observation_id": "obs-1"}],
        },
    )
    assert watch.status_code == 200
    assert watch.json()["result_status"] == "matched"

    churn = client.post(
        "/operational-policies/evaluate",
        json={
            "policy_key": "netpay.store.churn_candidate",
            "subject_type": "store",
            "subject_id": "S-10",
            "facts": {"inactive_days": 60, "open_service_case": False, "open_replacement": False},
            "evidence_references": [{"observation_id": "obs-2"}],
        },
    )
    assert churn.status_code == 200
    assert churn.json()["result_status"] == "matched"

    insufficient = client.post(
        "/operational-policies/evaluate",
        json={
            "policy_key": "netpay.store.churn_candidate",
            "subject_type": "store",
            "subject_id": "S-11",
            "facts": {"inactive_days": 62},
            "evidence_references": [{"observation_id": "obs-3"}],
        },
    )
    assert insufficient.status_code == 200
    assert insufficient.json()["result_status"] == "insufficient_data"

    critical = client.post(
        "/operational-policies/evaluate",
        json={
            "policy_key": "netpay.store.critical_sales_drop",
            "subject_type": "store",
            "subject_id": "S-12",
            "facts": {"historical_volume": 5000, "sales_drop_percentage": 40},
            "evidence_references": [{"observation_id": "obs-4"}],
        },
    )
    assert critical.status_code == 200
    assert critical.json()["result_status"] == "matched"

    asset = client.post(
        "/operational-policies/evaluate",
        json={
            "policy_key": "netpay.asset.recovery_review",
            "subject_type": "asset",
            "subject_id": "TPV-1",
            "facts": {"is_churn_candidate": True, "asset_assigned": True, "active_shipment_or_replacement": False},
            "evidence_references": [{"observation_id": "obs-5"}],
        },
    )
    assert asset.status_code == 200
    assert asset.json()["result_status"] == "matched"

    evaluations_after = client.get("/policy-evaluations").json()
    assert len(evaluations_after) >= len(evaluations_before) + 5

    summary = client.get("/mission-control/summary")
    assert summary.status_code == 200
    payload = summary.json()
    assert payload["policy_matches"] >= 4
    assert payload["insufficient_data_evaluations"] >= 1


def test_days_since_operator_evaluation():
    old_date = (datetime.now(timezone.utc) - timedelta(days=45)).isoformat()
    response = client.post(
        "/operational-policies",
        json={
            "policy_key": "custom.days.since",
            "domain": "netpay",
            "version": 1,
            "status": "active",
            "description": "days since check",
            "severity": "warning",
            "requires_human_approval": True,
            "configuration": {"conditions": [{"field": "last_sale_at", "operator": "days_since_greater_than", "value": 30}]},
        },
    )
    assert response.status_code == 201

    eval_response = client.post(
        "/operational-policies/evaluate",
        json={
            "policy_key": "custom.days.since",
            "subject_type": "store",
            "subject_id": "S-99",
            "facts": {"last_sale_at": old_date},
            "evidence_references": [],
        },
    )
    assert eval_response.status_code == 200
    assert eval_response.json()["result_status"] == "matched"
