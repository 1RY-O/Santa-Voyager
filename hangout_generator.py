from __future__ import annotations

from models import ConstraintInput, ConstraintCheckResult, HangoutOutput
from constraints import check_hangout_constraints
from ai_provider import create_provider


def generate_hangout(
    location: str,
    budget_str: str | None,
    available_time: str,
    interests: list[str],
    dislikes: list[str],
    group_size: int,
    indoor_pref: bool,
    outdoor_pref: bool,
    accessibility_needs: str,
) -> tuple[HangoutOutput, ConstraintCheckResult]:
    """Generate a hangout plan using the AI provider, then validate constraints."""

    # Build constraint input (budget already validated upstream; parse defensively)
    budget_float = None
    if budget_str:
        try:
            budget_float = float(
                budget_str.strip().replace("$", "").replace(",", "").strip()
            )
        except ValueError:
            budget_float = None

    prefs = [p for p in interests if p]
    if accessibility_needs and accessibility_needs.strip():
        prefs = prefs + ["wheelchair-accessible" if "wheelchair" in accessibility_needs.lower() else "accessibility-friendly"]
    constraints = ConstraintInput(
        must_avoid=[d for d in dislikes if d],
        preferences=prefs,
        budget_limit=budget_float,
    )

    # Build prompts for AI
    system_prompt = """You are a creative hangout/plan generator. Generate exactly one plan idea that fits the user's constraints.
Return a valid JSON object with these exact fields: title, vibe, activities, budget_breakdown, constraints_satisfied, assumptions.
- title: A creative plan title
- vibe: Overall vibe/atmosphere (e.g., "Relaxed and romantic", "Energetic and fun")
- activities: List of activity objects with "name" and "duration" fields (e.g., [{"name": "Activity name", "duration": "30 min"}])
- budget_breakdown: Approximate total budget with currency (e.g., "$50-75 total")
- constraints_satisfied: List of constraints this plan satisfies
- assumptions: List of assumptions the user should verify

Be concise. Ensure the plan respects budget limits, respects dislikes, and matches activity preferences (indoor/outdoor)."""

    user_prompt = f"""Generate a hangout plan with these constraints:

LOCATION: {location}
BUDGET: ${budget_str or 'Not specified'}
AVAILABLE TIME: {available_time}
INTERESTS: {interests or 'None'}
DISLIKES: {dislikes or 'None'}
GROUP SIZE: {group_size}
INDOOR PREFERRED: {indoor_pref}
OUTDOOR PREFERRED: {outdoor_pref}
ACCESSIBILITY NEEDS: {accessibility_needs or 'None'}

Generate the hangout plan now."""

    # Create provider (demo or live)
    provider = create_provider()
    
    try:
        raw_response = provider.generate(
            system_prompt, user_prompt, temperature=0.7
        )
        hangout_data = provider.parse_json(raw_response)
        
        # Validate against Pydantic schema
        hangout = HangoutOutput(**hangout_data)
        
    except Exception:
        print("AI generation failed, using fallback")
        hangout = HangoutOutput(
            title="Rooftop Sunset Picnic",
            vibe="Relaxed and romantic",
            activities=[
                {"name": "Setup picnic blanket", "duration": "15 min"},
                {"name": "Wine and cheese tasting", "duration": "45 min"},
                {"name": "Watch sunset", "duration": "30 min"},
                {"name": "Stargazing", "duration": "60 min"},
            ],
            budget_breakdown="$50-75 total",
            constraints_satisfied=["budget-friendly", "outdoor", "evening"],
            assumptions=["Verify weather and reservation requirements"],
        )
    
    # Check constraints
    constraint_result = check_hangout_constraints(hangout, constraints)
    
    return hangout, constraint_result


def generate_demo_hangout(constraints: ConstraintInput) -> tuple[HangoutOutput, ConstraintCheckResult]:
    """Generate a demo hangout plan with realistic hardcoded output."""
    hangout = HangoutOutput(
        title="Rooftop Sunset Picnic",
        vibe="Relaxed and romantic",
        activities=[
            {"name": "Setup picnic blanket", "duration": "15 min"},
            {"name": "Wine and cheese tasting", "duration": "45 min"},
            {"name": "Watch sunset", "duration": "30 min"},
            {"name": "Stargazing", "duration": "60 min"},
        ],
        budget_breakdown="$50-75 total",
        constraints_satisfied=["budget-friendly", "outdoor", "evening"],
        assumptions=["Verify weather and reservation requirements"],
    )
    constraint_result = check_hangout_constraints(hangout, constraints)
    return hangout, constraint_result
