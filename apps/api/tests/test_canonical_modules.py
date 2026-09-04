from yarvis_api.bootstrap import create_app
from yarvis_api.canonical_modules import canonical_modules
from yarvis_api.config import Settings
from yarvis_api.module_registry import ApplicationModule

CANONICAL_MODULE_IDS = (
    "platform",
    "identity",
    "governance",
    "relationship",
    "observation_evidence",
    "knowledge",
    "decision_intelligence",
    "execution",
    "operational_execution",
    "document_registry",
    "automation",
    "mission_control",
    "netpay_merchant_operations",
)


def test_canonical_module_baseline_is_explicit_and_immutable() -> None:
    modules = canonical_modules()

    assert tuple(module.module_id for module in modules) == CANONICAL_MODULE_IDS
    assert len({module.module_id for module in modules}) == len(modules)
    assert all(module.dependencies == () for module in modules)
    assert all(module.register_routes is None for module in modules)


def test_default_application_composes_the_canonical_module_baseline() -> None:
    app = create_app(Settings(environment="test"))

    assert app.state.yarvis.module_registry.is_sealed is True
    assert tuple(module.module_id for module in app.state.yarvis.module_registry.modules) == CANONICAL_MODULE_IDS


def test_explicit_modules_and_explicit_empty_modules_override_the_default_baseline() -> None:
    synthetic_module = ApplicationModule(module_id="test.synthetic", display_name="Synthetic")
    synthetic_app = create_app(Settings(environment="test"), modules=(synthetic_module,), contracts=())
    empty_app = create_app(Settings(environment="test"), modules=(), contracts=())
    later_default_app = create_app(Settings(environment="test"))

    assert tuple(module.module_id for module in synthetic_app.state.yarvis.module_registry.modules) == (
        "test.synthetic",
    )
    assert empty_app.state.yarvis.module_registry.modules == ()
    assert (
        tuple(module.module_id for module in later_default_app.state.yarvis.module_registry.modules)
        == CANONICAL_MODULE_IDS
    )
    assert synthetic_app.state.yarvis.module_registry is not empty_app.state.yarvis.module_registry
    assert empty_app.state.yarvis.module_registry is not later_default_app.state.yarvis.module_registry
