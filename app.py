from __future__ import annotations

import html
import os
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from models import ConstraintInput, InputValidator
from gift_generator import generate_gift
from hangout_generator import generate_hangout
from ai_provider import is_live_mode

st.set_page_config(
    page_title="The Ultimate Gift / Hangout Generator",
    page_icon="🎁",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .main { padding: 2rem 1rem; max-width: 1100px; }
    .stButton > button {
        width: 100%; background-color: #c0392b; color: #ffffff;
        border-radius: 8px; border: none; padding: 0.75rem 1rem;
        font-size: 1.05rem; font-weight: 600;
    }
    .stButton > button:hover { background-color: #a93226; }
    .stButton > button:focus-visible,
    input:focus-visible, select:focus-visible, textarea:focus-visible {
        outline: 3px solid #1a73e8 !important; outline-offset: 2px;
    }
    .result-card {
        background: #f8f9fa; border: 1px solid #dfe3e6; border-radius: 12px;
        padding: 1.5rem; margin-top: 1rem;
    }
    .constraint-violated {
        color: #7f1d1d; background: #fef2f2; border: 1px solid #b91c1c;
        padding: 0.5rem 1rem; border-radius: 6px; margin: 0.25rem 0; font-weight: 600;
    }
    .constraint-satisfied {
        color: #14532d; background: #f0fdf4; border: 1px solid #15803d;
        padding: 0.5rem 1rem; border-radius: 6px; margin: 0.25rem 0;
    }
    .demo-banner {
        background: #fffbeb; border: 1px solid #b45309; color: #78350f;
        border-radius: 8px; padding: 0.75rem 1rem; margin-bottom: 1rem; font-weight: 600;
    }
    .live-banner {
        background: #f0fdf4; border: 1px solid #15803d; color: #14532d;
        border-radius: 8px; padding: 0.75rem 1rem; margin-bottom: 1rem; font-weight: 600;
    }
    .empty-state {
        border: 1px dashed #9aa0a6; border-radius: 8px; padding: 1.25rem;
        color: #3c4043; margin-top: 1rem;
    }
    @media (max-width: 640px) {
        .main { padding: 1rem 0.5rem; }
        h1 { font-size: 1.5rem; }
    }
</style>
""", unsafe_allow_html=True)


def init_session_state() -> None:
    st.session_state.setdefault("mode", "gift")
    st.session_state.setdefault("last_gift", None)
    st.session_state.setdefault("last_hangout", None)
    st.session_state.setdefault("last_constraint_result", None)


def mode_banner(live: bool) -> None:
    if live:
        st.markdown(
            '<div class="live-banner" role="status">✅ Live mode — connected to Nebius AI.</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="demo-banner" role="status">🔓 Demo Mode — showing deterministic sample '
            "outputs. Add <code>NEBIUS_API_KEY</code> and set <code>APP_MODE=live</code> for real generation.</div>",
            unsafe_allow_html=True,
        )


def esc(text: object) -> str:
    return html.escape(str(text) if text is not None else "")


def render_constraint_blocks(result) -> None:
    if result is None:
        return
    for s in result.satisfied:
        st.markdown(f'<p class="constraint-satisfied">✅ {esc(s)}</p>', unsafe_allow_html=True)
    for v in result.violated:
        st.markdown(f'<p class="constraint-violated">⚠️ {esc(v)}</p>', unsafe_allow_html=True)
    for n in result.notes:
        st.markdown(f'<p style="color:#3c4043;font-size:0.9rem;">ℹ️ {esc(n)}</p>', unsafe_allow_html=True)


def render_gift_mode() -> None:
    st.title("🎁 Gift Generator")
    st.caption("Tell us about the person and occasion — hard constraints (budget, avoidances) are enforced, not just used as hints.")

    with st.form("gift_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            interests = st.text_input(
                "Interests / hobbies",
                placeholder="e.g., hiking, reading, cooking",
                help="What does the person enjoy? Comma-separated.",
            )
            occasion = st.text_input(
                "Occasion",
                placeholder="e.g., birthday, anniversary, graduation",
                help="What is the gift occasion?",
            )
            relationship = st.selectbox(
                "Relationship",
                ["Partner", "Friend", "Family member", "Child", "Colleague", "Other"],
                help="Your relationship to the recipient.",
            )
        with col2:
            dislikes = st.text_input(
                "Dislikes / avoidances",
                placeholder="e.g., green, crowds, wool",
                help="Must-avoid items. Comma-separated. These are strictly excluded.",
            )
            budget = st.text_input(
                "Budget in USD (optional)",
                placeholder="e.g., 20",
                help="Hard maximum in USD. Estimates above this are flagged.",
            )
        extra_details = st.text_area(
            "Extra details (optional)",
            placeholder="Style, sizes, favorite colors, allergies, etc.",
            height=90,
        )
        submitted = st.form_submit_button("Generate gift idea 🎁")

    if submitted:
        ok, err = InputValidator.validate_required_text(
            ("Interests", interests), ("Occasion", occasion), ("Relationship", relationship)
        )
        if not ok:
            st.error(err)
            return
        ok, err = InputValidator.validate_optional_text(
            ("Dislikes", dislikes), ("Extra details", extra_details)
        )
        if not ok:
            st.error(err)
            return
        ok, budget_val = InputValidator.validate_budget(budget)
        if not ok:
            st.error(budget_val)
            return
        dislikes_list = InputValidator.normalize_list(dislikes)
        interests_list = InputValidator.normalize_list(interests)
        with st.spinner("Generating your gift idea…"):
            try:
                gift, check = generate_gift(
                    must_have=[],
                    must_avoid=dislikes_list,
                    preferences=interests_list,
                    budget_str=budget_val or "",
                    occasion=occasion.strip(),
                    relationship=relationship.strip(),
                    extra_details=(extra_details or "").strip(),
                )
            except Exception:
                st.error("Something went wrong during generation. Please try again.")
                return
        st.session_state.last_gift = gift
        st.session_state.last_hangout = None
        st.session_state.last_constraint_result = check

    gift = st.session_state.last_gift
    check = st.session_state.last_constraint_result
    if gift is None:
        st.markdown(
            '<div class="empty-state">No results yet — fill in the form above and press <b>Generate gift idea</b>.</div>',
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f"""
        <div class="result-card" aria-live="polite">
            <h2>{esc(gift.title)}</h2>
            <p><strong>Estimated price:</strong> {esc(gift.estimated_price)}</p>
            <p><strong>Why it fits:</strong> {esc(gift.constraint_satisfied)}</p>
            <p><strong>Personalization idea:</strong> {esc(gift.personalization_idea)}</p>
            <p><strong>Categories:</strong> {esc(", ".join(gift.categories))}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_constraint_blocks(check)
    if st.button("Clear results & edit inputs"):
        st.session_state.last_gift = None
        st.session_state.last_constraint_result = None
        st.rerun()


def parse_group_size(raw: str) -> int:
    return 6 if raw.strip() == "6+" else int(raw)


def render_hangout_mode() -> None:
    st.title("🎯 Hangout Generator")
    st.caption("Tell us about your group — budget and avoidances are treated as hard constraints.")

    with st.form("hangout_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            location = st.text_input(
                "Location / city",
                placeholder="e.g., New York City",
                help="Where should the hangout happen?",
            )
            available_time = st.selectbox(
                "Available time",
                ["1-2 hours", "2-3 hours", "3-4 hours", "Half day", "Full day"],
                help="How much time do you have?",
            )
            group_size_raw = st.selectbox(
                "Group size",
                ["1", "2", "3", "4", "5", "6+"],
                help="Number of people attending.",
            )
            indoor_pref = st.checkbox("Prefer indoor", value=False)
        with col2:
            outdoor_pref = st.checkbox("Prefer outdoor", value=False)
            interests = st.text_input(
                "Interests (comma-separated)",
                placeholder="e.g., hiking, dining, museums",
                help="What does the group enjoy?",
            )
            dislikes = st.text_input(
                "Dislikes (comma-separated)",
                placeholder="e.g., crowds, loud venues",
                help="Must-avoid items. These are strictly excluded.",
            )
        budget = st.text_input(
            "Total budget in USD (optional)",
            placeholder="e.g., 50",
            help="Hard maximum total in USD.",
        )
        accessibility = st.text_input(
            "Accessibility needs (optional)",
            placeholder="e.g., wheelchair accessible step-free",
            help="Any accessibility requirements.",
        )
        submitted = st.form_submit_button("Generate hangout plan 🎯")

    if submitted:
        ok, err = InputValidator.validate_required_text(
            ("Location", location), ("Interests", interests), ("Available time", available_time)
        )
        if not ok:
            st.error(err)
            return
        ok, err = InputValidator.validate_optional_text(
            ("Dislikes", dislikes), ("Accessibility needs", accessibility)
        )
        if not ok:
            st.error(err)
            return
        ok, budget_val = InputValidator.validate_budget(budget)
        if not ok:
            st.error(budget_val)
            return
        with st.spinner("Generating your hangout plan…"):
            try:
                hangout, check = generate_hangout(
                    location=location.strip(),
                    budget_str=budget_val or "",
                    available_time=available_time,
                    interests=InputValidator.normalize_list(interests),
                    dislikes=InputValidator.normalize_list(dislikes),
                    group_size=parse_group_size(group_size_raw),
                    indoor_pref=indoor_pref,
                    outdoor_pref=outdoor_pref,
                    accessibility_needs=(accessibility or "").strip(),
                )
            except Exception:
                st.error("Something went wrong during generation. Please try again.")
                return
        st.session_state.last_hangout = hangout
        st.session_state.last_gift = None
        st.session_state.last_constraint_result = check

    hangout = st.session_state.last_hangout
    check = st.session_state.last_constraint_result
    if hangout is None:
        st.markdown(
            '<div class="empty-state">No results yet — fill in the form above and press <b>Generate hangout plan</b>.</div>',
            unsafe_allow_html=True,
        )
        return

    items = "".join(
        f"<li>{esc(a.get('name', '?'))} — {esc(a.get('duration', '?'))}</li>"
        for a in hangout.activities
    )
    st.markdown(
        f"""
        <div class="result-card" aria-live="polite">
            <h2>{esc(hangout.title)}</h2>
            <p><strong>Vibe:</strong> {esc(hangout.vibe)}</p>
            <p><strong>Plan:</strong></p>
            <ol style="margin-left:1rem;">{items}</ol>
            <p><strong>Budget:</strong> {esc(hangout.budget_breakdown)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_constraint_blocks(check)
    if hangout.assumptions:
        st.markdown("<p><strong>Please verify:</strong></p>", unsafe_allow_html=True)
        for a in hangout.assumptions:
            st.markdown(f"<p style='color:#3c4043;font-size:0.9rem;'>• {esc(a)}</p>", unsafe_allow_html=True)
    if st.button("Clear results & edit inputs"):
        st.session_state.last_hangout = None
        st.session_state.last_constraint_result = None
        st.rerun()


def main() -> None:
    init_session_state()
    live = is_live_mode()
    with st.sidebar:
        st.title("🎯 Generator Mode")
        mode = st.radio(
            "Select mode",
            ["Gift Generator", "Hangout Generator"],
            index=0 if st.session_state.mode == "gift" else 1,
            help="Choose gift ideas or hangout plans.",
        )
        st.session_state.mode = "gift" if mode == "Gift Generator" else "hangout"
        st.divider()
        st.caption("ℹ️ About")
        st.caption("Strict constraints: budget + avoidances are enforced and reported.")
        st.caption("✅ Live: Nebius AI" if live else "🔓 Demo: sample outputs (no key needed)")
    mode_banner(live)
    if st.session_state.mode == "gift":
        render_gift_mode()
    else:
        render_hangout_mode()


if __name__ == "__main__":
    main()
