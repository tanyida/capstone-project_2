"""Government-paid leave, broken down by how many children you have."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benefits import engine, leave, ui         # noqa: E402

ui.page_setup("Parental Leave", "\N{CALENDAR}")
ui.hero(
    "\N{CALENDAR} Government-Paid Leave",
    "How many days and weeks of paid leave you get, and how that changes with "
    "each child.",
)

children = ui.get_children()

# ---------------------------------------------------------------------------
# The rule everyone wants: days by number of children
# ---------------------------------------------------------------------------

st.markdown("#### Childcare leave scales with the number of children")
st.caption("Announced at NDR 2026. Today's Childcare Leave and Extended Childcare "
           "Leave merge into one scheme covering Singapore Citizen children aged 12 "
           "and below. The start date has not been announced yet.")

bands = st.columns(3)
band_specs = [
    ("1 child aged 12 and below", leave.childcare_leave_days(1), "#2563eb"),
    ("2 children aged 12 and below", leave.childcare_leave_days(2), "#0d9488"),
    ("3 or more children aged 12 and below", leave.childcare_leave_days(3), "#d946a0"),
]
for col, (label, days, colour) in zip(bands, band_specs):
    with col:
        st.markdown(
            f"""<div class="lw-card">
                   {ui.pill(label.split(' aged')[0], colour)}
                   <div class="lw-amount">{days} days</div>
                   <div class="lw-meta">per working parent, per year<br/>
                   <b>{days * 2} days</b> for a two-working-parent household</div>
                </div>""",
            unsafe_allow_html=True,
        )

st.markdown(
    f"<span class='lw-note'>Today the same household gets "
    f"{leave.CURRENT_CCL_DAYS} days a year while the youngest child is "
    f"{leave.CURRENT_CCL_MAX_AGE} or below, dropping to {leave.CURRENT_ECL_DAYS} days "
    f"once the youngest is {leave.CURRENT_CCL_MAX_AGE + 1} to "
    f"{leave.CURRENT_ECL_MAX_AGE}.</span>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Personalised schedule
# ---------------------------------------------------------------------------

st.markdown("---")
st.markdown("#### Your household, year by year")

if not children:
    ui.empty_state("Add your children on the **Benefits Calculator** page to see your "
                   "own leave entitlement for every year until the youngest turns 12.")
else:
    working_parents = st.radio(
        "Working parents in the household", [1, 2], index=1, horizontal=True,
        help="Childcare leave is an entitlement of each working parent.",
    )
    start_year = st.number_input(
        "Assumed start year for the merged childcare leave scheme",
        min_value=2026, max_value=2035,
        value=leave.ASSUMED_NEW_CCL_START_YEAR, step=1,
        help="The Government has said implementation details will be shared in early "
             "2027. Change this to see the effect of a later start.",
    )

    schedule = leave.childcare_leave_schedule(
        children, working_parents=working_parents, new_scheme_from=int(start_year))

    if schedule.empty:
        ui.empty_state("None of your children are aged 12 or below in the years "
                       "covered, so childcare leave no longer applies.")
    else:
        metrics = st.columns(3)
        metrics[0].metric("Total childcare leave days to come",
                          f"{int(schedule[schedule['Year'] >= date.today().year]['Household days (new scheme)'].sum())} days",
                          help="Household total from this year until the youngest "
                               "child turns 12.")
        metrics[1].metric("Extra days versus today's rules",
                          f"{int(schedule['Extra days gained'].sum())} days")
        metrics[2].metric("Peak year",
                          str(int(schedule.loc[schedule['Household days (new scheme)'].idxmax(), 'Year'])),
                          help="The year your household is entitled to the most "
                               "childcare leave.")

        melted = schedule.melt(
            id_vars="Year",
            value_vars=["Household days (new scheme)", "Household days (current rules)"],
            var_name="Scheme", value_name="Days",
        )
        melted["Scheme"] = melted["Scheme"].str.replace("Household days ", "", regex=False)
        chart = (
            alt.Chart(melted)
            .mark_bar()
            .encode(
                x=alt.X("Year:O", axis=alt.Axis(labelAngle=0)),
                y=alt.Y("Days:Q", title="Household leave days"),
                color=alt.Color(
                    "Scheme:N",
                    scale=alt.Scale(domain=["(new scheme)", "(current rules)"],
                                    range=["#2563eb", "#cbd5e1"]),
                    legend=alt.Legend(orient="top", title=None)),
                xOffset="Scheme:N",
                tooltip=["Year", "Scheme", "Days"],
            )
            .properties(height=300)
        )
        st.altair_chart(chart, **ui.stretch())
        display = schedule.copy()
        display["Year"] = display["Year"].astype(int).astype(str)
        st.dataframe(display, **ui.stretch(), hide_index=True)

# ---------------------------------------------------------------------------
# Leave at each birth
# ---------------------------------------------------------------------------

st.markdown("---")
st.markdown("#### Paid leave in the child's first year")

if children:
    births = leave.birth_leave(children)
    rows = []
    for entry in births:
        rows.append({
            "Child": entry.child,
            "Born": entry.year,
            "Maternity (weeks)": entry.maternity,
            "Paternity (weeks)": entry.paternity,
            "Shared Parental Leave (weeks)": entry.shared,
            "Total (weeks)": entry.total,
        })
    table = pd.DataFrame(rows)
    table["Born"] = table["Born"].astype(int).astype(str)
    st.dataframe(table, **ui.stretch(), hide_index=True)
    st.caption("Shared Parental Leave was phased in: 6 weeks for children born on or "
               "after 1 Apr 2025 and 10 weeks for children born on or after 1 Apr 2026. "
               "Children born earlier get none.")
else:
    cols = st.columns(4)
    cols[0].metric("Maternity leave", f"{leave.MATERNITY_WEEKS} weeks")
    cols[1].metric("Paternity leave", f"{leave.PATERNITY_WEEKS} weeks")
    cols[2].metric("Shared Parental Leave", "10 weeks")
    cols[3].metric("Total for the couple", "30 weeks")

# ---------------------------------------------------------------------------
# Reference cards
# ---------------------------------------------------------------------------

st.markdown("---")
st.markdown("#### Every leave scheme at a glance")
cards = leave.leave_scheme_cards()
for start in range(0, len(cards), 3):
    row = st.columns(3)
    for col, card in zip(row, cards[start:start + 3]):
        with col:
            st.markdown(
                f"""<div class="lw-card">
                       <h4>{card['name']}</h4>
                       <div class="lw-amount" style="font-size:1.25rem">{card['amount']}</div>
                       <div class="lw-meta"><b>{card['who']}</b><br/>{card['detail']}</div>
                    </div>""",
                unsafe_allow_html=True,
            )
    st.write("")

st.info("The Government covers the cost of all child-related leave - maternity, "
        "paternity, adoption, Shared Parental Leave and childcare leave - for every "
        "birth order, up to the reimbursement cap.", icon="\N{INFORMATION SOURCE}")

ui.disclaimer()
