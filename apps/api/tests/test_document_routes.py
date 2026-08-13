from uuid import uuid4

from fastapi.testclient import TestClient

from yarvis_api.clock import utc_now
from yarvis_api.main import app
from yarvis_api.models.organization import Organization
from yarvis_api.models.principal import Principal, PrincipalMembership


client = TestClient(app)
ORGANIZATION_ID = uuid4()
OTHER_ORGANIZATION_ID = uuid4()


_SUBJECTS = {
    "document.read": "document:viewer",
    "document.create": "document:contributor",
    "document.metadata.update": "document:contributor",
    "document.version.add": "document:contributor",
    "document.association.link": "document:contributor",
    "document.association.unlink": "document:contributor",
    "document.archive": "document:archivist",
}


def headers(authority, organization_id=ORGANIZATION_ID, *, subject=None):
    resolved_subject = subject or _SUBJECTS[authority]
    if organization_id == OTHER_ORGANIZATION_ID:
        resolved_subject += "-other"
    return {
        "x-yarvis-subject": resolved_subject,
        "x-yarvis-actor": "forged-document-actor",
        "x-yarvis-organization": str(organization_id),
        "x-yarvis-authority": authority,
        "x-yarvis-auth-token": "deterministic-inbound-intake",
    }


def request_payload(key, **changes):
    payload = {"title": "Route document", "classification": "general", "visibility": "organization", "media_type": "text/plain", "checksum_algorithm": "sha256", "checksum_value": "a" * 64, "storage_provider": "external", "storage_key": None, "external_reference": "urn:route:document", "source_kind": "manual", "provenance": {"source": "route"}, "original_filename": "route.txt", "byte_size": 1, "source_reference": "route", "idempotency_key": key, "correlation_id": str(uuid4())}
    payload.update(changes)
    return payload


def setup_organizations(clean_database):
    with app.state.yarvis.persistence.create_session() as session:
        session.add_all([Organization(id=ORGANIZATION_ID, legal_name="Route documents", display_name="Route documents"), Organization(id=OTHER_ORGANIZATION_ID, legal_name="Other route documents", display_name="Other route documents")])
        session.flush()
        for subject, organization_id, role in (
            ("document:viewer", ORGANIZATION_ID, "document_viewer"),
            ("document:contributor", ORGANIZATION_ID, "document_contributor"),
            ("document:archivist", ORGANIZATION_ID, "document_archivist"),
            ("document:other-domain", ORGANIZATION_ID, "inbound_operator"),
            ("document:viewer-other", OTHER_ORGANIZATION_ID, "document_viewer"),
            ("document:contributor-other", OTHER_ORGANIZATION_ID, "document_contributor"),
            ("document:archivist-other", OTHER_ORGANIZATION_ID, "document_archivist"),
        ):
            principal = Principal(external_subject=subject, status="active")
            session.add(principal)
            session.flush()
            session.add(PrincipalMembership(principal_id=principal.id, organization_id=organization_id, role=role))
        session.commit()


def test_document_routes_commands_replay_and_queries(clean_database):
    setup_organizations(clean_database)
    create = request_payload("route-create")
    first = client.post("/documents", json=create, headers=headers("document.create"))
    replay = client.post("/documents", json=create, headers=headers("document.create"))
    assert first.status_code == replay.status_code == 201 and first.json()["id"] == replay.json()["id"]
    document_id = first.json()["id"]
    conflict = client.post("/documents", json=request_payload("route-create", title="changed"), headers=headers("document.create"))
    assert conflict.status_code == 409
    update = client.patch(f"/documents/{document_id}", json={"title": "Updated", "classification": "technical", "visibility": "organization", "expected_version": 1, "idempotency_key": "route-update", "correlation_id": str(uuid4())}, headers=headers("document.metadata.update"))
    assert update.status_code == 200 and update.json()["title"] == "Updated"
    version_payload = request_payload("route-version", checksum_value="b" * 64, expected_version=2)
    for field in ("title", "classification", "visibility"):
        version_payload.pop(field)
    version = client.post(f"/documents/{document_id}/versions", json=version_payload, headers=headers("document.version.add"))
    assert version.status_code == 201 and version.json()["sequence"] == 2
    versions = client.get(f"/documents/{document_id}/versions", headers=headers("document.read"))
    assert versions.status_code == 200 and [item["sequence"] for item in versions.json()] == [1, 2]
    linked = client.post(f"/documents/{document_id}/associations", json={"subject_type": "organization", "subject_id": str(ORGANIZATION_ID), "idempotency_key": "route-link", "correlation_id": str(uuid4())}, headers=headers("document.association.link"))
    assert linked.status_code == 201
    linked_replay = client.post(f"/documents/{document_id}/associations", json={"subject_type": "organization", "subject_id": str(ORGANIZATION_ID), "idempotency_key": "route-link", "correlation_id": str(uuid4())}, headers=headers("document.association.link"))
    assert linked_replay.status_code == 201 and linked_replay.json()["id"] == linked.json()["id"]
    associations = client.get(f"/documents/{document_id}/associations", headers=headers("document.read"))
    assert associations.status_code == 200 and len(associations.json()) == 1
    subject = client.get(f"/documents/subjects/organization/{ORGANIZATION_ID}", headers=headers("document.read"))
    assert subject.status_code == 200 and [item["id"] for item in subject.json()["items"]] == [document_id]
    unlinked = client.post(f"/documents/{document_id}/associations/{linked.json()['id']}/unlink", json={"idempotency_key": "route-unlink", "correlation_id": str(uuid4())}, headers=headers("document.association.unlink"))
    assert unlinked.status_code == 200 and unlinked.json()["unlinked_at"] is not None
    unlinked_replay = client.post(f"/documents/{document_id}/associations/{linked.json()['id']}/unlink", json={"idempotency_key": "route-unlink", "correlation_id": str(uuid4())}, headers=headers("document.association.unlink"))
    assert unlinked_replay.status_code == 200 and unlinked_replay.json()["id"] == linked.json()["id"]
    archive = client.post(f"/documents/{document_id}/archive", json={"idempotency_key": "route-archive", "correlation_id": str(uuid4()), "expected_version": 3}, headers=headers("document.archive"))
    assert archive.status_code == 200 and archive.json()["lifecycle_status"] == "archived"
    document = client.get(f"/documents/{document_id}", headers=headers("document.read"))
    assert document.status_code == 200 and document.json()["active_association_count"] == 0


def test_document_routes_conceal_tenants_and_register_openapi(clean_database):
    setup_organizations(clean_database)
    created = client.post("/documents", json=request_payload("route-foreign"), headers=headers("document.create", OTHER_ORGANIZATION_ID))
    assert created.status_code == 201
    foreign = client.get(f"/documents/{created.json()['id']}", headers=headers("document.read"))
    missing = client.get(f"/documents/{uuid4()}", headers=headers("document.read"))
    assert (foreign.status_code, foreign.json()["message"]) == (404, "document not found")
    assert (missing.status_code, missing.json()["message"]) == (404, "document not found")
    denied = client.get(
        f"/documents/{created.json()['id']}",
        headers=headers("document.read", subject="document:other-domain"),
    )
    assert denied.status_code == 403
    schema = client.get("/openapi.json").json()
    paths = schema["paths"]
    assert "/documents" in paths and "/documents/{document_id}/versions" in paths and "/documents/subjects/{subject_type}/{subject_id}" in paths
    operation_ids = [operation["operationId"] for methods in paths.values() for operation in methods.values() if "operationId" in operation]
    assert len(operation_ids) == len(set(operation_ids))
    contract_ids = {contract.interaction_contract_id for contract in app.state.yarvis.contract_registry.list()}
    assert {f"IC-DOCUMENT-CMD-00{number}" for number in range(1, 7)} | {f"IC-DOCUMENT-QRY-00{number}" for number in range(1, 5)} <= contract_ids
    assert [module.module_id for module in app.state.yarvis.module_registry.modules].count("document_registry") == 1


def test_document_route_authority_is_persisted_and_revocation_takes_effect(clean_database):
    setup_organizations(clean_database)
    forged_elevation = client.post(
        "/documents",
        json=request_payload("forged-elevation"),
        headers=headers("document.create", subject="document:viewer"),
    )
    assert forged_elevation.status_code == 403

    created = client.post(
        "/documents",
        json=request_payload("persisted-contributor"),
        headers=headers("document.archive", subject="document:contributor"),
    )
    assert created.status_code == 201
    document_id = created.json()["id"]

    forged_organization_headers = headers("document.read")
    forged_organization_headers["x-yarvis-organization"] = str(OTHER_ORGANIZATION_ID)
    forged_organization = client.get(f"/documents/{document_id}", headers=forged_organization_headers)
    assert forged_organization.status_code == 200

    with app.state.yarvis.persistence.create_session() as session:
        membership = session.query(PrincipalMembership).join(Principal).filter(
            Principal.external_subject == "document:viewer"
        ).one()
        membership.status = "revoked"
        membership.revoked_at = utc_now()
        session.commit()

    replay_after_revocation = client.get(
        f"/documents/{document_id}", headers=headers("document.read")
    )
    assert replay_after_revocation.status_code == 403
