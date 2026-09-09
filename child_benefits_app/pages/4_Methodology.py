"""How the projection is built, and what it assumes."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benefits import catalogue as cat          # noqa: E402
from benefits import leave, ui                 # noqa: E402

ui.page_setup("Methodology", "\N{MEMO}")
ui.hero(
    "\N{MEMO} Methodology and assumptions",
    "Every number in this app is traceable to a published rule or a stated "
    "assumption. Here is both.",
)

st.markdown("""
#### How the calculator works

1. You enter each child's name and date of birth. Birth order is worked out by
   sorting the children by date of birth.
2. Each benefit rule is applied to each child independently, producing one row per
   payout, per calendar year.
3. Rows are tagged **Cash**, **Education** or **Healthcare** by the account the money
   lands in, and marked *received* or *upcoming* by comparing the payout date with
   today.
4. The dashboard, the yearly table and the charts are all views over that same set of
   rows, so the totals always reconcile.

A Singapore Citizen child born under the full package projects to
**""" + ui.money_md(cat.HEADLINE_TOTAL) + """** from birth to age 17: """ +
ui.money_md(cat.SG_CHILD_SUPPORT_PACKAGE_TOTAL) + """ from the SG Child Support
Package, """ + ui.money_md(cat.MEDISAVE_GRANT_NEWBORN) + """ from the MediSave Grant
for Newborns and about """ + ui.money_md(cat.EDUSAVE_TOTAL) + """ in Edusave
contributions.
""")

st.markdown("---")
st.markdown("#### Assumptions")

assumptions = [
    ("CDA co-matching",
     f"The Government matches CDA savings dollar for dollar up to "
     f"{ui.money_md(cat.CDA_COMATCH_CAP)}, so this money only arrives if you save. The "
     f"app assumes you earn the full cap by default (adjustable in the sidebar) and "
     f"spreads it evenly from birth to age {cat.CDA_COMATCH_SPREAD_LAST_AGE}, when "
     f"most families draw on the account. Matching is actually available until the "
     f"child turns {cat.CDA_COMATCH_LAST_AGE}."),
    ("Baby Gift tranches",
     "The $10,000 Baby Gift is paid in two tranches within 12 months of birth. The "
     "app splits it evenly and puts the second tranche in the following calendar "
     "year for children born in the second half of the year."),
    ("Older children's Baby Bonus",
     "For children whose Baby Bonus Cash Gift finished before the package started, "
     "the app shows the cohort total in the birth year as a single estimated figure "
     "rather than reconstructing every instalment."),
    ("Edusave rates",
     f"Held flat at {ui.money_md(cat.EDUSAVE_PRIMARY_PER_YEAR)} a year in primary school "
     f"and {ui.money_md(cat.EDUSAVE_SECONDARY_PER_YEAR)} in secondary school. These have "
     f"been revised upward before and may be again."),
    ("Childcare leave start date",
     f"The merged childcare leave scheme has no announced start date. The app assumes "
     f"{leave.ASSUMED_NEW_CCL_START_YEAR}, which you can change on the Parental Leave "
     f"page."),
    ("Inflation and future revisions",
     "All figures are in today's dollars and no inflation adjustment is applied. "
     "Schemes are revised regularly, so long-range totals are indicative."),
    ("What is excluded",
     "Means-tested subsidies (preschool, healthcare, housing grants), tax reliefs "
     "such as Parenthood Tax Rebate, Qualifying Child Relief and Working Mother's "
     "Child Relief, and the cheaper childcare fees announced for 2028 to 2030. These "
     "depend on income and circumstances, and including them would double count "
     "against the payouts shown."),
]

for title, body in assumptions:
    with st.expander(title):
        st.write(body)

st.markdown("---")
st.markdown("#### Confidence flags")
st.markdown("""
| Flag | Meaning |
| --- | --- |
| **Confirmed** | Taken directly from the announced scheme rules. |
| **Estimated** | Reconstructed past payouts, or amounts that depend on your own saving. |
| **Conditional** | Announced but not finalised - the exact rules are still being worked out. |
""")

st.markdown("---")
ui.sources_block()

st.markdown("---")
st.markdown("#### Privacy")
st.markdown(
    "Children's names and dates of birth are held in Streamlit session state for the "
    "duration of your browser session only. Nothing is written to disk, sent to a "
    "third party or logged."
)

ui.disclaimer()
