from __future__ import annotations

from models import ConstraintInput, ConstraintCheckResult, GiftOutput
from constraints import check_gift_constraints
from ai_provider import create_provider


def generate_gift(
    must_have: list[str],
    must_avoid: list[str],
    preferences: list[str],
    budget_str: str | None,
    occasion: str,
    relationship: str,
    extra_details: str,
) -> tuple[GiftOutput, ConstraintCheckResult]:
    """Generate a gift idea using the AI provider, then validate constraints."""

    # Build constraint input (budget already validated upstream; parse defensively)
    budget_float = None
    if budget_str:
        try:
            budget_float = float(
                budget_str.strip().replace("$", "").replace(",", "").strip()
            )
        except ValueError:
            budget_float = None

    constraints = ConstraintInput(
        must_have=must_have,
        must_avoid=must_avoid,
        preferences=preferences,
        budget_limit=budget_float,
    )

    # Build prompts for AI
    system_prompt = """You are a thoughtful gift curator. Generate exactly one gift idea that fits the user's constraints.
Return a valid JSON object with these exact fields: title, estimated_price, constraint_satisfied, personalization_idea, categories.
- title: A creative gift title
- estimated_price: Price range with currency symbol (e.g., "$45-65")
- constraint_satisfied: Which specific user constraint this gift satisfies
- personalization_idea: A practical personalization or presentation idea
- categories: 2-3 relevant categories/tags

Be concise. Ensure the gift respects budget limits and avoids must_avoid items."""
    
    user_prompt = f"""Generate a gift idea with these constraints:

MUST-HAVE: {must_have or 'None'}
MUST-AVOID: {must_avoid or 'None'}
PREFERENCES: {preferences or 'None'}
OCCASION: {occasion}
RELATIONSHIP: {relationship}
EXTRA DETAILS: {extra_details or 'None'}
BUDGET: ${budget_str or 'Not specified'}

Generate the gift now."""
    
    # Create provider (demo or live)
    provider = create_provider()
    
    try:
        raw_response = provider.generate(
            system_prompt, user_prompt, temperature=0.7
        )
        gift_data = provider.parse_json(raw_response)
        
        # Validate against Pydantic schema
        gift = GiftOutput(**gift_data)
        
    except Exception:
        # Fallback to structured default if AI fails (no prompt/response logging)
        print("AI generation failed, using fallback")
        gift = GiftOutput(
            title="Custom Gift Certificate",
            estimated_price="$25-40",
            constraint_satisfied="flexible within budget",
            personalization_idea="Certificate valid for any occasion",
            categories=["experience", "flexible"],
        )
    
    # Check constraints
    constraint_result = check_gift_constraints(gift, constraints)
    
    return gift, constraint_result


def generate_demo_gift(constraints: ConstraintInput) -> tuple[GiftOutput, ConstraintCheckResult]:
    """Generate a demo gift with realistic hardcoded output."""
    gift = GiftOutput(
        title="Custom Engraved Leather Wallet",
        estimated_price="$45-65",
        constraint_satisfied="personalized with recipient's initials",
        personalization_idea="Engrave their initials and a short meaningful date",
        categories=["accessories", "personalized"],
    )
    constraint_result = check_gift_constraints(gift, constraints)
    return gift, constraint_result
