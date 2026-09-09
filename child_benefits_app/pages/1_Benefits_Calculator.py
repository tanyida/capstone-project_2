"""Enter children and get a full year-by-year benefits projection."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benefits import catalogue as cat          # noqa: E402
from benefits import engine, ui                # noqa: E402

ui.page_setup("Benefits Calculator", "\N{POCKET CALCULATOR}")
ui.hero(
    "\N{POCKET CALCULATOR} Benefits Calculator",
    "Enter each child's name and date of birth to see exactly what they are "
    "entitled to, and when it lands.",
)

assumptions = ui.assumption_controls("calc")

st.markdown("#### Step 1 - Tell us about your children")
st.caption("Expecting? Use the due date. Nothing is saved to a server; the entries "
           "live only in this browser session.")
children = ui.child_editor("calculator")

if not children:
    ui.empty_state("Add at least one child above to run the calculator.")
    ui.disclaimer()
    st.stop()

frame = engine.project(children, assumptions)

if frame.empty:
    ui.empty_state(
        "None of the children entered qualify for these benefits. Almost every "
        "scheme here requires the child to be a Singapore Citizen."
    )
    ui.disclaimer()
    st.stop()

# ---------------------------------------------------------------------------
# Step 2 - the summary
# ---------------------------------------------------------------------------

st.markdown("---")
st.markdown("#### Step 2 - Your total projected benefits")

totals = engine.category_totals(frame)
received, upcoming = engine.split_by_status(frame)
grand_total = float(frame["amount"].sum())

top = st.columns([1.4, 1, 1])
top[0].markdown(
    f"""<div class="lw-card lw-stat">
           <div class="lw-meta">Total across {len(children)} """
    f"""{'child' if len(children) == 1 else 'children'}</div>
           <div class="lw-amount" style="font-size:2.3rem">{ui.money(grand_total)}</div>
           <div class="lw-meta">Birth to age 17, under currently announced rules</div>
        </div>""",
    unsafe_allow_html=True,
)
top[1].metric("Already received", ui.money(received))
top[2].metric("Still to come", ui.money(upcoming))

st.write("")
ui.category_cards(totals)

# ---------------------------------------------------------------------------
# Step 3 - the breakdowns
# ---------------------------------------------------------------------------

st.markdown("---")
st.markdown("#### Step 3 - Broken down")

tab_year, tab_child, tab_benefit, tab_detail = st.tabs(
    ["By year", "By child", "By benefit", "Every payout"])

with tab_year:
    st.altair_chart(ui.yearly_stacked_chart(frame, height=340),
                    **ui.stretch())
    pivot = engine.yearly_summary(frame)
    ui.yearly_table(pivot)

with tab_child:
    st.altair_chart(ui.per_child_chart(frame), **ui.stretch())
    per_child = (
        frame.pivot_table(index="child", columns="category", values="amount",
                          aggfunc="sum", fill_value=0.0)
        .reindex(columns=cat.CATEGORIES, fill_value=0.0)
    )
    per_child["Total"] = per_child.sum(axis=1)
    st.dataframe(
        per_child.reset_index().rename(columns={"child": "Child"}).style.format(
            {c: "${:,.0f}" for c in cat.CATEGORIES + ["Total"]}),
        **ui.stretch(), hide_index=True,
    )

with tab_benefit:
    summary = engine.benefit_totals(frame)
    display = summary.copy()
    display["Total"] = display["Total"].map(ui.money)
    st.dataframe(display, **ui.stretch(), hide_index=True)
    st.caption("'Paid into' matters: only the cash rows can be spent on anything. "
               "CDA, Edusave, PSEA and MediSave money is ring-fenced for approved uses.")

with tab_detail:
    chosen = st.multiselect("Filter by child", sorted(frame["child"].unique()),
                            default=sorted(frame["child"].unique()))
    categories = st.multiselect("Filter by category", cat.CATEGORIES,
                                default=cat.CATEGORIES)
    view = frame[frame["child"].isin(chosen) & frame["category"].isin(categories)]
    view = view.rename(columns={
        "child": "Child", "year": "Year", "age": "Age turning", "benefit": "Benefit",
        "category": "Category", "vehicle": "Paid into", "amount": "Amount",
        "status": "Status", "confidence": "Confidence", "note": "Notes",
    })
    view["Year"] = view["Year"].astype(int).astype(str)
    view["Amount"] = view["Amount"].map(ui.money)
    st.dataframe(view, **ui.stretch(), hide_index=True)
    st.download_button(
        "Download this projection as CSV",
        data=view.to_csv(index=False).encode("utf-8"),
        file_name="child_benefits_projection.csv", mime="text/csv",
    )
    st.caption("**Confidence**: *Confirmed* figures come straight from the announced "
               "scheme rules. *Estimated* figures reconstruct past payouts or depend "
               "on your own saving. *Conditional* figures are announced but not yet "
               "finalised.")

ui.disclaimer()
