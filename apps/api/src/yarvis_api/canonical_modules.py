"""Explicit canonical context-module declarations for Yarvis composition."""

from yarvis_api.module_registry import ApplicationModule

CANONICAL_MODULES: tuple[ApplicationModule, ...] = (
    ApplicationModule(module_id="identity", display_name="Identity"),
    ApplicationModule(module_id="governance", display_name="Governance"),
    ApplicationModule(module_id="relationship", display_name="Relationship"),
    ApplicationModule(module_id="observation_evidence", display_name="Observation & Evidence"),
    ApplicationModule(module_id="knowledge", display_name="Knowledge"),
    ApplicationModule(module_id="decision_intelligence", display_name="Decision Intelligence"),
    ApplicationModule(module_id="execution", display_name="Execution"),
    ApplicationModule(module_id="operational_execution", display_name="Operational Execution"),
    ApplicationModule(module_id="document_registry", display_name="Document Registry"),
    ApplicationModule(module_id="automation", display_name="Automation"),
    ApplicationModule(module_id="mission_control", display_name="Mission Control"),
    ApplicationModule(module_id="netpay_merchant_operations", display_name="Netpay Merchant Operations"),
)


def canonical_modules() -> tuple[ApplicationModule, ...]:
    """Return the immutable, explicit canonical module composition baseline."""

    return CANONICAL_MODULES
