"""Shared presentation helpers: styling, the child editor and charts."""

from __future__ import annotations

import inspect
from datetime import date

import altair as alt
import pandas as pd
import streamlit as st

from . import catalogue as cat
from .engine import Child, Assumptions, RECEIVED, UPCOMING

APP_TITLE = "Little Wins"
APP_TAGLINE = "Every government benefit your child is entitled to, year by year."

CSS = """
<style>
  .lw-hero {
    background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 55%, #0d9488 100%);
    color: #fff; padding: 1.6rem 1.8rem; border-radius: 16px; margin-bottom: 1.2rem;
  }
  .lw-hero h1 { color: #fff; font-size: 1.9rem; margin: 0 0 .3rem 0; }
  .lw-hero p { color: rgba(255,255,255,.88); margin: 0; font-size: 1rem; }
  .lw-card {
    border: 1px solid rgba(49,51,63,.16); border-radius: 14px; padding: 1rem 1.1rem;
    height: 100%; background: rgba(255,255,255,.55);
  }
  .lw-card h4 { margin: .1rem 0 .35rem 0; font-size: 1rem; }
  .lw-card .lw-amount { font-size: 1.5rem; font-weight: 700; line-height: 1.2; }
  .lw-card .lw-meta { font-size: .82rem; opacity: .75; margin-top: .35rem; }
  .lw-pill {
    display: inline-block; padding: .12rem .55rem; border-radius: 999px;
    font-size: .72rem; font-weight: 600; color: #fff; letter-spacing: .01em;
  }
  .lw-note { font-size: .84rem; opacity: .8; }
  .lw-stat { border-left: 4px solid #2563eb; padding-left: .9rem; }
</style>
"""


def _accepts_width(fn) -> bool:
    """Streamlit 1.49 renamed ``use_container_width`` to ``width``."""
    try:
        return "width" in inspect.signature(fn).parameters
    except (TypeError, ValueError):
        return False


_USE_WIDTH_API = _accepts_width(st.dataframe)


def stretch() -> dict:
    """Kwargs that make a widget fill its container, on old and new Streamlit."""
    return {"width": "stretch"} if _USE_WIDTH_API else {"use_container_width": True}


def page_setup(page_title: str, icon: str = "\N{BABY}") -> None:
    st.set_page_config(page_title=f"{page_title} - {APP_TITLE}",
                       page_icon=icon, layout="wide")
    st.markdown(CSS, unsafe_allow_html=True)


def hero(title: str, subtitle: str) -> None:
    st.markdown(
        f'<div class="lw-hero"><h1>{title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )


def pill(text: str, colour: str) -> str:
    return f'<span class="lw-pill" style="background:{colour}">{text}</span>'


def money(value: float) -> str:
    """Plain money string. Use for dataframes and st.metric."""
    return f"${value:,.0f}"


def money_md(value: float) -> str:
    """Money for st.markdown / st.write.

    Streamlit reads a matched pair of ``$`` as inline LaTeX, so two amounts in
    one markdown block would silently render as maths. Escaping the sign keeps
    it as text.

    Only for plain markdown and inline HTML. Inside a block-level HTML element
    such as a ``<div>`` the markdown escape is not processed and the backslash
    shows up on screen - use :func:`money` there.
    """
    return "\\" + money(value)


# ---------------------------------------------------------------------------
# Children held in session state
# ---------------------------------------------------------------------------

STATE_KEY = "children"
ASSUMPTION_KEY = "assumptions"


def get_children() -> list[Child]:
    rows = st.session_state.get(STATE_KEY, [])
    children = [
        Child(name=r["name"], dob=r["dob"], citizen=r.get("citizen", True))
        for r in rows if r.get("name") and r.get("dob")
    ]
    return sorted(children, key=lambda c: c.dob)


def set_children(rows: list[dict]) -> None:
    st.session_state[STATE_KEY] = rows


def get_assumptions() -> Assumptions:
    stored = st.session_state.get(ASSUMPTION_KEY)
    return stored if isinstance(stored, Assumptions) else Assumptions()


def set_assumptions(assumptions: Assumptions) -> None:
    st.session_state[ASSUMPTION_KEY] = assumptions


def child_editor(key: str = "editor") -> list[Child]:
    """A small add / remove form for children. Returns the current children."""
    rows = st.session_state.get(STATE_KEY, [])

    with st.form(f"{key}_add", clear_on_submit=True):
        cols = st.columns([3, 2, 2, 1.4])
        name = cols[0].text_input("Child's name", placeholder="e.g. Amelia")
        dob = cols[1].date_input(
            "Date of birth", value=date.today(),
            min_value=date(2005, 1, 1), max_value=date(date.today().year + 6, 12, 31),
            help="Expecting? Enter the due date to see what the child will receive.",
        )
        citizen = cols[2].selectbox(
            "Citizenship", ["Singapore Citizen", "Not a Singapore Citizen"],
            help="Almost every benefit here requires the child to be a Singapore Citizen.",
        )
        cols[3].markdown("<div style='height:1.8rem'></div>", unsafe_allow_html=True)
        submitted = cols[3].form_submit_button("Add child", **stretch(),
                                               type="primary")
    if submitted:
        if not name.strip():
            st.warning("Give the child a name so you can tell them apart in the charts.")
        else:
            rows = rows + [{
                "name": name.strip(), "dob": dob,
                "citizen": citizen == "Singapore Citizen",
            }]
            set_children(rows)
            st.rerun()

    if rows:
        st.markdown("##### Your children")
        for index, row in enumerate(sorted(rows, key=lambda r: r["dob"])):
            actual_index = rows.index(row)
            line = st.columns([3, 2, 2, 1.4])
            line[0].markdown(f"**{row['name']}**")
            line[1].markdown(row["dob"].strftime("%d %b %Y"))
            age = date.today().year - row["dob"].year
            status = "Singapore Citizen" if row.get("citizen", True) else "Non-citizen"
            if row["dob"] > date.today():
                when = f"Due {row['dob'].strftime('%b %Y')}"
            elif age == 0:
                when = "Born this year"
            else:
                when = f"Turns {age} this year"
            line[2].markdown(
                f"<span class='lw-note'>{when} &middot; {status}</span>",
                unsafe_allow_html=True,
            )
            if line[3].button("Remove", key=f"{key}_rm_{actual_index}",
                              **stretch()):
                rows.pop(actual_index)
                set_children(rows)
                st.rerun()
    return get_children()


def assumption_controls(key: str = "assume") -> Assumptions:
    """Sidebar controls for the things the projection has to assume."""
    current = get_assumptions()
    st.sidebar.markdown("### Projection settings")
    ratio = st.sidebar.slider(
        "How much of the $5,000 CDA co-matching cap will you use?",
        min_value=0, max_value=100, value=int(current.cda_match_ratio * 100), step=10,
        format="%d%%", key=f"{key}_ratio",
        help="The Government matches your CDA savings dollar for dollar, so this "
             "part of the package only arrives if you actually save into the account.",
    ) / 100
    edusave = st.sidebar.checkbox(
        "Include Edusave contributions", value=current.include_edusave,
        key=f"{key}_edusave",
        help="$230 a year in primary school and $290 in secondary school.",
    )
    medisave = st.sidebar.checkbox(
        "Include MediSave Grant for Newborns", value=current.include_medisave_grant,
        key=f"{key}_medisave",
    )
    large_family = st.sidebar.checkbox(
        "Include Large Family MediSave Grant", value=current.include_large_family_medisave,
        key=f"{key}_lfmg",
        help="$5,000 for the third and later child. Its extension to large families "
             "that have not received it is still being studied, so it is off by default.",
    )
    assumptions = Assumptions(
        cda_match_ratio=ratio,
        include_edusave=edusave,
        include_medisave_grant=medisave,
        include_large_family_medisave=large_family,
    )
    set_assumptions(assumptions)
    return assumptions


# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

_SCALE = alt.Scale(domain=cat.CATEGORIES,
                   range=[cat.CATEGORY_COLOURS[c] for c in cat.CATEGORIES])


def yearly_stacked_chart(frame: pd.DataFrame, height: int = 320) -> alt.Chart:
    """Stacked bars: one bar per calendar year, split by benefit category."""
    data = (frame.groupby(["year", "category"], as_index=False)["amount"].sum())
    return (
        alt.Chart(data)
        .mark_bar(cornerRadiusTopLeft=3, cornerRadiusTopRight=3)
        .encode(
            x=alt.X("year:O", title="Calendar year",
                    axis=alt.Axis(labelAngle=0, labelOverlap=True)),
            y=alt.Y("amount:Q", title="Benefits received",
                    axis=alt.Axis(format="$,.0f")),
            color=alt.Color("category:N", title="Category", scale=_SCALE,
                            legend=alt.Legend(orient="top")),
            tooltip=[
                alt.Tooltip("year:O", title="Year"),
                alt.Tooltip("category:N", title="Category"),
                alt.Tooltip("amount:Q", title="Amount", format="$,.0f"),
            ],
        )
        .properties(height=height)
    )


def cumulative_chart(frame: pd.DataFrame, height: int = 260) -> alt.Chart:
    """How the running total builds up over the years."""
    by_year = frame.groupby("year", as_index=False)["amount"].sum().sort_values("year")
    by_year["cumulative"] = by_year["amount"].cumsum()
    return (
        alt.Chart(by_year)
        .mark_area(line={"color": "#2563eb"}, opacity=0.28, color="#2563eb")
        .encode(
            x=alt.X("year:O", title="Calendar year",
                    axis=alt.Axis(labelAngle=0, labelOverlap=True)),
            y=alt.Y("cumulative:Q", title="Cumulative benefits",
                    axis=alt.Axis(format="$,.0f")),
            tooltip=[
                alt.Tooltip("year:O", title="Year"),
                alt.Tooltip("cumulative:Q", title="Received to date", format="$,.0f"),
            ],
        )
        .properties(height=height)
    )


def per_child_chart(frame: pd.DataFrame, height: int = 300) -> alt.Chart:
    """Total per child, split by category."""
    data = frame.groupby(["child", "category"], as_index=False)["amount"].sum()
    return (
        alt.Chart(data)
        .mark_bar(cornerRadiusTopRight=3, cornerRadiusBottomRight=3)
        .encode(
            y=alt.Y("child:N", title=None, sort="-x"),
            x=alt.X("amount:Q", title="Total benefits", axis=alt.Axis(format="$,.0f")),
            color=alt.Color("category:N", title="Category", scale=_SCALE,
                            legend=alt.Legend(orient="top")),
            tooltip=[
                alt.Tooltip("child:N", title="Child"),
                alt.Tooltip("category:N", title="Category"),
                alt.Tooltip("amount:Q", title="Amount", format="$,.0f"),
            ],
        )
        .properties(height=height)
    )


def category_cards(totals: dict[str, float]) -> None:
    cols = st.columns(len(cat.CATEGORIES))
    for col, category in zip(cols, cat.CATEGORIES):
        with col:
            st.markdown(
                f"""<div class="lw-card">
                       {pill(category, cat.CATEGORY_COLOURS[category])}
                       <div class="lw-amount">{money(totals.get(category, 0))}</div>
                       <div class="lw-meta">{cat.CATEGORY_BLURB[category]}</div>
                    </div>""",
                unsafe_allow_html=True,
            )


def yearly_table(pivot: pd.DataFrame) -> None:
    display = pivot.copy()
    display["Year"] = display["Year"].astype(int).astype(str)
    for column in cat.CATEGORIES + ["Total"]:
        display[column] = display[column].map(money)
    st.dataframe(display, **stretch(), hide_index=True)


def empty_state(message: str) -> None:
    st.info(message, icon="\N{ELECTRIC LIGHT BULB}")


def disclaimer() -> None:
    with st.expander("Disclaimer - please read"):
        st.markdown(cat.DISCLAIMER)


def sources_block() -> None:
    st.markdown("##### Where these numbers come from")
    for label, url in cat.SOURCES:
        st.markdown(f"- [{label}]({url})")
