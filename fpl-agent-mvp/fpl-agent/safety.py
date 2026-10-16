"""Fail-closed proposal gate. No transaction execution is implemented."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Policy:
    no_automatic_hits: bool = True
    no_automatic_chips: bool = True
    validate_budget_rules: bool = True
    deadline_freeze_minutes: int = 15
    prevent_duplicates: bool = True
    emergency_stop: bool = True  # Must be explicitly disengaged for approval workflows.

def evaluate(*, policy, points_hit, chip, budget_valid, rules_valid,
             minutes_to_deadline, data_fresh, action_id, processed_ids):
    reasons = []
    if policy.emergency_stop: reasons.append('Emergency stop is engaged')
    if policy.no_automatic_hits and points_hit > 0: reasons.append('Points hit prohibited')
    if policy.no_automatic_chips and chip: reasons.append('Chip activation prohibited')
    if policy.validate_budget_rules and (not budget_valid or not rules_valid):
        reasons.append('Budget/rules check failed')
    if minutes_to_deadline is None or minutes_to_deadline <= policy.deadline_freeze_minutes:
        reasons.append('Deadline safety freeze or unknown deadline')
    if not data_fresh: reasons.append('Data not fresh')
    if policy.prevent_duplicates and action_id in processed_ids: reasons.append('Duplicate action')
    return {'eligible_for_manual_review': not reasons, 'reasons': reasons,
            'execution_available': False}
