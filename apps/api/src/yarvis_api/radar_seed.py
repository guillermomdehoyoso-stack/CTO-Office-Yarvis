"""Explicit local demonstration seed for the Netpay operational radar.

Run only on a developer machine: ``docker compose exec api python -m yarvis_api.radar_seed``.
It is never called by application startup or production deployment.
"""

from datetime import timedelta

from sqlalchemy import select

from yarvis_api.api.routes.radar import ECOMMERCE_TEMPLATE, TPV_TEMPLATE, activity, now
from yarvis_api.database import legacy_session
from yarvis_api.models.radar import RadarChecklistItem, RadarMerchant, RadarRequest

WORKSPACE = "netpay-demo"
ACTOR = "demo-seed"


def add_request(session, merchant: RadarMerchant, *, text: str, classification: str, products: list[str], priority: str = "normal", next_action: str | None = None, due_days: int | None = None, closed: bool = False) -> None:
    request = RadarRequest(workspace_id=WORKSPACE, merchant_id=merchant.id, free_text=text, classification=classification, priority=priority, owner="Guillermo", next_action=next_action, due_at=now() + timedelta(days=due_days) if due_days is not None else None)
    if closed:
        request.status, request.closed_at, request.next_action = "closed", now(), None
    session.add(request); session.flush()
    template = ECOMMERCE_TEMPLATE if classification == "alta_ecommerce" else TPV_TEMPLATE if classification == "alta_tpv" else []
    for position, (code, label) in enumerate(template, 1):
        session.add(RadarChecklistItem(request_id=request.id, item_code=code, label=label, position=position, received=closed, received_by=ACTOR if closed else None, received_at=now() if closed else None))
    activity(session, merchant, request, "request_created", "Solicitud demostrativa creada", ACTOR)
    if closed: activity(session, merchant, request, "request_closed", "Solicitud demostrativa cerrada", ACTOR)


def seed() -> int:
    with legacy_session() as session:
        if session.scalar(select(RadarMerchant).where(RadarMerchant.workspace_id == WORKSPACE)):
            return 0
        tpv = RadarMerchant(workspace_id=WORKSPACE, trade_name="Café Horizonte", contact_name="Operación demo", products=["tpv"])
        ecommerce = RadarMerchant(workspace_id=WORKSPACE, trade_name="Gasolinera La Providencia", contact_name="Operación demo", products=["ecommerce"])
        replacement = RadarMerchant(workspace_id=WORKSPACE, trade_name="Farmacia del Centro", contact_name="Operación demo", products=["tpv"])
        mixed = RadarMerchant(workspace_id=WORKSPACE, trade_name="Mercado Alameda", contact_name="Operación demo", products=["tpv", "ecommerce"])
        session.add_all([tpv, ecommerce, replacement, mixed]); session.flush()
        for item in (tpv, ecommerce, replacement, mixed): activity(session, item, None, "merchant_created", "Comercio demostrativo registrado", ACTOR)
        add_request(session, tpv, text="Alta TPV concluida.", classification="alta_tpv", products=["tpv"], closed=True)
        add_request(session, ecommerce, text="Gasolinera La Providencia solicita alta e-commerce. Ya envió constancia fiscal y estado de cuenta; falta INE, comprobante de domicilio, fotos del establecimiento y dominio.", classification="alta_ecommerce", products=["ecommerce"], priority="high", next_action="Solicitar INE y comprobante de dominio", due_days=2)
        add_request(session, replacement, text="Reposición de terminal por falla física.", classification="reposicion_terminal", products=["tpv"], priority="high", next_action="Confirmar envío de terminal", due_days=-2)
        add_request(session, mixed, text="Alta TPV terminada.", classification="alta_tpv", products=["tpv"], closed=True)
        add_request(session, mixed, text="Pendiente de documentos para e-commerce.", classification="alta_ecommerce", products=["ecommerce"], next_action="Recibir comprobante de dominio", due_days=1)
        session.commit()
    return 4


if __name__ == "__main__":
    created = seed()
    print("Radar demo created: 4 merchants" if created else "Radar demo already present; no records changed")
