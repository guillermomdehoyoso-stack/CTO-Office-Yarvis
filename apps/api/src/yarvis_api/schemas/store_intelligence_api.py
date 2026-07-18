from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from yarvis_api.schemas.store_intelligence import StoreOperationalProfile

@dataclass(frozen=True)
class StoreProfilePage:
    items: list[StoreOperationalProfile]; total: int; limit: int; offset: int

@dataclass(frozen=True)
class StoreIntelligenceSummary:
    total_profiles: int; pending_profiles: int; actionable_recovery_profiles: int; evidence_review_profiles: int; activation_failures: int; operational_blocks: int; cancellation_reviews: int; reactivation_with_history: int; reactivation_without_history: int; terminal_recovery_candidates: int; historical_only_profiles: int; incomplete_profiles: int; generated_at: datetime | None
