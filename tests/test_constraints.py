from models import ConstraintInput, GiftOutput, HangoutOutput
from constraints import check_gift_constraints, check_hangout_constraints


def _gift(price="$45-65", title="Custom Engraved Leather Wallet"):
    return GiftOutput(
        title=title,
        estimated_price=price,
        constraint_satisfied="personalized pick",
        personalization_idea="Engrave initials",
        categories=["accessories"],
    )


def test_gift_over_budget_strict_uses_upper_bound():
    c = ConstraintInput(must_avoid=[], budget_limit=20.0)
    r = check_gift_constraints(_gift("$45-65"), c)
    assert not r.passed and any("Over budget" in v for v in r.violated)


def test_gift_within_budget():
    c = ConstraintInput(must_avoid=[], budget_limit=100.0)
    r = check_gift_constraints(_gift("$45-65"), c)
    assert r.passed


def test_gift_must_avoid():
    c = ConstraintInput(must_avoid=["green"], budget_limit=None)
    r = check_gift_constraints(_gift(title="Green Wool Scarf"), c)
    assert not r.passed and any("green" in v.lower() for v in r.violated)


def _hangout(breakdown="$50-75 total"):
    return HangoutOutput(
        title="Rooftop Sunset Picnic",
        vibe="Relaxed",
        activities=[
            {"name": "Setup picnic blanket", "duration": "15 min"},
            {"name": "Watch sunset", "duration": "30 min"},
        ],
        budget_breakdown=breakdown,
        constraints_satisfied=["outdoor"],
        assumptions=["Verify weather"],
    )


def test_hangout_over_budget():
    c = ConstraintInput(must_avoid=[], budget_limit=20.0)
    r = check_hangout_constraints(_hangout(), c)
    assert not r.passed


def test_hangout_avoidance_and_env():
    c = ConstraintInput(must_avoid=["crowds"], preferences=["outdoor"], budget_limit=None)
    h = _hangout()
    h.activities = [{"name": "Downtown crowds festival", "duration": "2 hours"}]
    r = check_hangout_constraints(h, c)
    assert not r.passed
    assert any("crowds" in v.lower() for v in r.violated)
