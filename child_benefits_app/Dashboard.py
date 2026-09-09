"""Little Wins - Singapore child benefits dashboard.

Run with:  streamlit run child_benefits_app/Dashboard.py
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

from benefits import catalogue as cat          # noqa: E402
from benefits import engine, leave, ui         # noqa: E402

ui.page_setup("Dashboard")

children = ui.get_children()
assumptions = ui.assumption_controls("dash")

ui.hero(
    "\N{BABY} " + ui.APP_TITLE,
    ui.APP_TAGLINE,
)

# ---------------------------------------------------------------------------
# Headline: what the SG Child Support Package is worth
# ---------------------------------------------------------------------------

if children:
    frame = engine.project(children, assumptions)
    totals = engine.category_totals(frame)
    received, upcoming = engine.split_by_status(frame)
    subject = f"{len(children)} child" if len(children) == 1 else f"{len(children)} children"
    st.markdown(f"### Your family at a glance &nbsp;<span class='lw-note'>"
                f"{subject} entered</span>", unsafe_allow_html=True)
else:
    reference = engine.reference_child()
    frame = engine.project([reference], assumptions)
    totals = engine.category_totals(frame)
    received, upcoming = engine.split_by_status(frame)
    st.markdown("### What one Singapore Citizen child receives, birth to age 17")
    ui.empty_state(
        "This is the standard picture for a child born under the SG Child Support "
        "Package. Add your own children on the **Benefits Calculator** page (or in "
        "the box further down) to see dates, ages and totals for your family."
    )

top = st.columns([1.3, 1, 1, 1])
top[0].markdown(
    f"""<div class="lw-card lw-stat">
           <div class="lw-meta">Total projected benefits</div>
           <div class="lw-amount" style="font-size:2.1rem">{ui.money(frame['amount'].sum())}</div>
           <div class="lw-meta">Across {int(frame['year'].nunique())} calendar years</div>
        </div>""",
    unsafe_allow_html=True,
)
top[1].metric("Already received", ui.money(received),
              help="Payouts whose scheduled date has already passed.")
top[2].metric("Still to come", ui.money(upcoming),
              help="Everything from today onwards, under current announced rules.")
top[3].metric("Cash in hand", ui.money(totals[cat.CASH]),
              help="The portion paid straight to your bank account.")

st.write("")
ui.category_cards(totals)

# ---------------------------------------------------------------------------
# Year-by-year view
# ---------------------------------------------------------------------------

st.markdown("---")
left, right = st.columns([3, 2])

with left:
    st.markdown("#### Benefits by year")
    st.caption("Each bar is one calendar year, split into cash, education and "
               "healthcare support.")
    st.altair_chart(ui.yearly_stacked_chart(frame), **ui.stretch())

with right:
    st.markdown("#### How the total builds up")
    st.caption("The running total from the first payout to the last.")
    st.altair_chart(ui.cumulative_chart(frame, height=320), **ui.stretch())

peak = frame.groupby("year")["amount"].sum()
biggest_year = int(peak.idxmax())
st.markdown(
    f"<span class='lw-note'>Biggest single year: <b>{biggest_year}</b> at "
    f"<b>{ui.money_md(peak.max())}</b>. Smallest: <b>{int(peak.idxmin())}</b> at "
    f"<b>{ui.money_md(peak.min())}</b>.</span>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# The benefits themselves
# ---------------------------------------------------------------------------

st.markdown("---")
st.markdown("#### Every benefit in the projection")
summary = engine.benefit_totals(frame)
display = summary.copy()
display["Total"] = display["Total"].map(ui.money)
st.dataframe(display, **ui.stretch(), hide_index=True)

if children:
    st.markdown("#### Split by child")
    st.altair_chart(ui.per_child_chart(frame), **ui.stretch())

# ---------------------------------------------------------------------------
# Leave snapshot
# ---------------------------------------------------------------------------

st.markdown("---")
st.markdown("#### Government-paid leave")

if children:
    schedule = leave.childcare_leave_schedule(children)
    births = leave.birth_leave(children)
    this_year = schedule[schedule["Year"] == date.today().year]
    if this_year.empty and not schedule.empty:
        this_year = schedule.head(1)

    cols = st.columns(3)
    if not this_year.empty:
        row = this_year.iloc[0]
        cols[0].metric(
            f"Childcare leave in {int(row['Year'])}",
            f"{int(row['Days per parent (new scheme)'])} days per parent",
            delta=f"{int(row['Extra days gained'])} extra household days"
                  if row["Extra days gained"] else None,
            help="Under the merged childcare leave scheme announced at NDR 2026.",
        )
        cols[1].metric("Household total",
                       f"{int(row['Household days (new scheme)'])} days",
                       help="Assuming two working parents.")
    total_weeks = sum(b.total for b in births)
    cols[2].metric("Paid parental leave at each birth",
                   f"{births[-1].total} weeks" if births else "-",
                   help=f"{total_weeks} weeks in total across all your children.")
    st.caption("Full year-by-year leave planning is on the **Parental Leave** page.")
else:
    cols = st.columns(3)
    cols[0].metric("Childcare leave", "8 to 12 days",
                   help="Per working parent per year, scaling with the number of "
                        "children aged 12 and below.")
    cols[1].metric("Paid leave in baby's first year", "30 weeks",
                   help="16 weeks maternity + 4 weeks paternity + 10 weeks Shared "
                        "Parental Leave for a child born on or after 1 Apr 2026.")
    cols[2].metric("Unpaid infant care leave", "12 days",
                   help="Per working parent per year, until the child turns 2.")

# ---------------------------------------------------------------------------
# Quick add
# ---------------------------------------------------------------------------

st.markdown("---")
st.markdown("#### Add your children")
st.caption("Nothing is stored anywhere - the entries live only in this browser session.")
ui.child_editor("dashboard")

st.markdown("---")
ui.sources_block()
ui.disclaimer()
