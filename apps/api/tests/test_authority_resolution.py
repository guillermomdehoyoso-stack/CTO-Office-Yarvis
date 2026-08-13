from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from yarvis_api.application.authority import permissions_for_role
from yarvis_api.application.errors import ApplicationError, ApplicationErrorCode
from yarvis_api.models.organization import Organization
from yarvis_api.models.principal import Principal, PrincipalMembership
from yarvis_api.services.authority_resolution import AuthorityResolutionService


def _resolved(session, *, memberships=1, status="active", organization_status="active"):
    principal = Principal(external_subject="local:ana", status=status)
    session.add(principal)
    organizations = [Organization(legal_name=f"Org {i}", display_name=f"Org {i}", status=organization_status) for i in range(memberships)]
    session.add_all(organizations); session.flush()
    session.add_all([PrincipalMembership(principal_id=principal.id, organization_id=org.id, role="radar_operator") for org in organizations]); session.commit()
    return principal, organizations


def test_closed_role_matrix_and_unknown_role_denial():
    assert "radar.read" in permissions_for_role("radar_viewer")
    with pytest.raises(ApplicationError) as error: permissions_for_role("header-admin")
    assert error.value.code == ApplicationErrorCode.AUTHORIZATION_DENIED


def test_document_registry_roles_are_closed_and_separated():
    assert permissions_for_role("document_viewer") == frozenset({"document.read"})
    assert permissions_for_role("document_contributor") == frozenset({
        "document.read",
        "document.create",
        "document.metadata.update",
        "document.version.add",
        "document.association.link",
        "document.association.unlink",
    })
    assert permissions_for_role("document_archivist") == frozenset({"document.read", "document.archive"})
    assert "document.read" not in permissions_for_role("inbound_operator")


def test_resolver_selects_persisted_membership_and_ignores_header_claims():
    from yarvis_api.main import app
    with app.state.yarvis.persistence.create_session() as session:
        principal, organizations = _resolved(session)
        envelope = AuthorityResolutionService().resolve(session, external_subject=principal.external_subject, selector=None, authentication_source="local-test", correlation_id="c1")
        assert envelope.organization_id == organizations[0].id
        assert "radar.request.close" in envelope.validated_permissions


def test_resolver_denials_and_selector_concealment():
    from yarvis_api.main import app
    with app.state.yarvis.persistence.create_session() as session:
        service = AuthorityResolutionService()
        with pytest.raises(ApplicationError): service.resolve(session, external_subject="header-actor", selector=None, authentication_source="local", correlation_id="c")
        principal, organizations = _resolved(session, memberships=2)
        with pytest.raises(ApplicationError) as ambiguous: service.resolve(session, external_subject=principal.external_subject, selector=None, authentication_source="local", correlation_id="c")
        assert ambiguous.value.code == ApplicationErrorCode.CONFLICT
        with pytest.raises(ApplicationError) as foreign: service.resolve(session, external_subject=principal.external_subject, selector=uuid4(), authentication_source="local", correlation_id="c")
        assert foreign.value.code == ApplicationErrorCode.RESOURCE_NOT_FOUND
        assert service.resolve(session, external_subject=principal.external_subject, selector=organizations[1].id, authentication_source="local", correlation_id="c").organization_id == organizations[1].id


def test_database_constraints_and_revoked_membership_is_not_active():
    from yarvis_api.main import app
    with app.state.yarvis.persistence.create_session() as session:
        principal, organizations = _resolved(session)
        session.add(Principal(external_subject=principal.external_subject))
        with pytest.raises(IntegrityError): session.commit()
        session.rollback()
        membership = session.query(PrincipalMembership).filter_by(principal_id=principal.id).one()
        membership.status = "revoked"; membership.revoked_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc); session.commit()
        with pytest.raises(ApplicationError): AuthorityResolutionService().resolve(session, external_subject=principal.external_subject, selector=None, authentication_source="local", correlation_id="c")
