from __future__ import annotations

from enum import Enum
from pydantic import BaseModel, Field, field_validator
from typing import Dict, List, Optional


class ConstraintCategory(Enum):
    MUST_HAVE = "must_have"
    MUST_AVOID = "must_avoid"
    PREFERENCE = "preference"
    BUDGET_LIMIT = "budget_limit"


class ConstraintInput(BaseModel):
    """Raw user input for constraints, validated on both client and server."""

    must_have: List[str] = Field(default_factory=list, description="Items that must be included")
    must_avoid: List[str] = Field(default_factory=list, description="Items that must be excluded")
    preferences: List[str] = Field(default_factory=list, description="Nice-to-have preferences")
    budget_limit: Optional[float] = Field(
        default=None, description="Maximum budget in USD (e.g., 20 for $20)"
    )
    budget_currency: str = Field(default="USD", description="Currency for budget limit")


class ConstraintCheckResult(BaseModel):
    """Result of checking a generated output against constraints."""

    passed: bool = False
    violated: List[str] = Field(default_factory=list, description="Constraints that were violated")
    satisfied: List[str] = Field(default_factory=list, description="Constraints that were satisfied")
    notes: List[str] = Field(default_factory=list, description="Additional notes about constraint handling")


class GiftOutput(BaseModel):
    """Structured output schema for gift generation."""

    title: str = Field(..., description="Gift title/name")
    estimated_price: str = Field(..., description="Estimated price range")
    constraint_satisfied: str = Field(
        ..., description="Which user constraint this satisfies"
    )
    personalization_idea: str = Field(
        ..., description="Practical personalization or presentation idea"
    )
    categories: List[str] = Field(
        default_factory=list, description="Gift categories/tags"
    )

    @field_validator("estimated_price")
    @classmethod
    def price_must_contain_range(cls, v: str) -> str:
        if not any(c in v for c in ["$", "USD", "free", "under"]):
            raise ValueError("estimated_price should include currency or price indication")
        return v


class HangoutOutput(BaseModel):
    """Structured output schema for hangout/plan generation."""

    title: str = Field(..., description="Plan title")
    vibe: str = Field(..., description="Overall vibe/atmosphere")
    activities: List[Dict[str, str]] = Field(
        default_factory=list, description="Sequence of activities with durations"
    )
    budget_breakdown: str = Field(
        default="", description="Approximate budget breakdown"
    )
    constraints_satisfied: List[str] = Field(
        default_factory=list, description="Constraints satisfied by this plan"
    )
    assumptions: List[str] = Field(
        default_factory=list, description="Assumptions the user should verify"
    )


class InputValidator:
    """Handles input validation for the Streamlit app."""

    MAX_INPUT_LENGTH = 500
    MAX_BUDGET = 10000  # $10,000 hard limit
    MIN_BUDGET = 0.01

    @classmethod
    def normalize_list(cls, raw: str | None) -> list[str]:
        """Split comma-separated input, strip whitespace, drop empties."""
        if not raw:
            return []
        return [p.strip() for p in raw.split(",") if p.strip()][:20]

    @classmethod
    def normalize_budget(cls, raw: str | None) -> str | None:
        """Normalize budget string; return None when empty."""
        if raw is None:
            return None
        cleaned = raw.strip().replace("$", "").replace(",", "").strip()
        return cleaned or None

    @classmethod
    def validate_budget(cls, budget_str: str | None) -> tuple[bool, str | None]:
        """Validate budget string is a positive number within limits.

        Returns (ok, normalized_or_error). Empty/None means 'no limit' -> (True, None).
        """
        cleaned = cls.normalize_budget(budget_str)
        if cleaned is None:
            return True, None
        try:
            val = float(cleaned)
        except ValueError:
            return False, "Budget must be a valid number (e.g. 20 for $20)."
        if val < cls.MIN_BUDGET:
            return False, f"Budget must be at least ${cls.MIN_BUDGET}"
        if val > cls.MAX_BUDGET:
            return False, f"Budget must not exceed ${cls.MAX_BUDGET}"
        return True, str(val)

    @classmethod
    def validate_required_text(
        cls, *named_inputs: tuple[str, str]
    ) -> tuple[bool, str | None]:
        """Validate required (label, value) pairs are non-empty and within limits."""
        for label, text in named_inputs:
            if not text or not text.strip():
                return False, f"{label} is required."
            if len(text.strip()) > cls.MAX_INPUT_LENGTH:
                return False, f"{label} is too long (max {cls.MAX_INPUT_LENGTH} chars)."
        return True, None

    @classmethod
    def validate_optional_text(
        cls, *named_inputs: tuple[str, str | None]
    ) -> tuple[bool, str | None]:
        """Validate optional (label, value) pairs are within length limits."""
        for label, text in named_inputs:
            if text and len(text) > cls.MAX_INPUT_LENGTH:
                return False, f"{label} is too long (max {cls.MAX_INPUT_LENGTH} chars)."
        return True, None
