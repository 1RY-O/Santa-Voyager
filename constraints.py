from __future__ import annotations

import re
from models import (
    ConstraintInput,
    ConstraintCheckResult,
    GiftOutput,
    HangoutOutput,
)


def check_gift_constraints(
    gift: GiftOutput, constraints: ConstraintInput
) -> ConstraintCheckResult:
    """Check a generated gift against the user's constraints."""
    violated = []
    satisfied = []
    notes = []

    # Check budget constraint (strict: upper end of a range must fit)
    if constraints.budget_limit is not None:
        numbers = re.findall(r"\d+(?:\.\d+)?", gift.estimated_price.replace(",", ""))
        if numbers:
            try:
                price_val = max(float(n) for n in numbers)
                if price_val > constraints.budget_limit:
                    violated.append(
                        f"Over budget: up to ~${price_val:g} exceeds your ${constraints.budget_limit:g} limit."
                    )
                else:
                    satisfied.append(
                        f"Within budget: up to ~${price_val:g} (limit ${constraints.budget_limit:g})."
                    )
            except ValueError:
                notes.append("Could not parse a price from the estimate; verify cost manually.")
        else:
            notes.append("Could not parse a price from the estimate; verify cost manually.")

    # Check must_avoid items
    gift_title_lower = gift.title.lower()
    for item in constraints.must_avoid:
        term = item.strip().lower()
        if term and term in gift_title_lower:
            violated.append(f"Contains avoided item: '{item.strip()}'")

    # Check must_have items (if provided)
    for item in constraints.must_have:
        term = item.strip().lower()
        if term and term not in gift_title_lower:
            notes.append(
                f"Missing requested element: '{item}' not found in gift title"
            )

    # General constraint satisfaction reporting
    if gift.constraint_satisfied:
        satisfied.append(gift.constraint_satisfied)

    passed = len(violated) == 0

    return ConstraintCheckResult(
        passed=passed,
        violated=violated,
        satisfied=satisfied,
        notes=notes,
    )


def check_hangout_constraints(
    hangout: HangoutOutput, constraints: ConstraintInput
) -> ConstraintCheckResult:
    """Check a generated hangout plan against the user's constraints."""
    violated = []
    satisfied = []
    notes = []

    # Check budget constraint (strict: upper end of a range must fit)
    if constraints.budget_limit is not None:
        amounts = re.findall(r"\d+(?:\.\d+)?", hangout.budget_breakdown.replace(",", ""))
        if amounts:
            total = max(float(a) for a in amounts)
            if total > constraints.budget_limit:
                violated.append(
                    f"Over budget: ~${total:g} exceeds your ${constraints.budget_limit:g} limit."
                )
            else:
                satisfied.append(
                    f"Within budget: ~${total:g} (limit ${constraints.budget_limit:g})."
                )
        else:
            notes.append("Could not parse a total from the budget breakdown; verify costs manually.")

    # Check must_avoid items in activities
    for activity in hangout.activities:
        activity_name = activity.get("name", "").lower()
        for item in constraints.must_avoid:
            term = item.strip().lower()
            if term and term in activity_name:
                violated.append(
                    f"Activity '{activity.get('name', '?')}' contains avoided item: '{item.strip()}'"
                )

    # Check indoor/outdoor preference
    if constraints.preferences:
        prefs_lower = [p.lower() for p in constraints.preferences]
        outdoor_keywords = {"outdoor", "outside", "garden", "park", "hiking"}
        indoor_keywords = {"indoor", "inside", "home", "office"}
        detected_env = []
        for act in hangout.activities:
            name = act.get("name", "").lower()
            if any(kw in name for kw in outdoor_keywords):
                detected_env.append("outdoor")
            if any(kw in name for kw in indoor_keywords):
                detected_env.append("indoor")
        # If user has strong preference and plan contradicts it
        if "outdoor" in prefs_lower and "outdoor" not in detected_env:
            violated.append(
                "Plan appears to be indoor-biased but you prefer outdoor activities"
            )
        if "indoor" in prefs_lower and "indoor" not in detected_env:
            violated.append(
                "Plan appears to be outdoor-biased but you prefer indoor activities"
            )

    passed = len(violated) == 0

    return ConstraintCheckResult(
        passed=passed,
        violated=violated,
        satisfied=satisfied,
        notes=notes,
    )
