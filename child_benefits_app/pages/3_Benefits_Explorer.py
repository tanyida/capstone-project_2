"""Reference view: every benefit, and how the new package maps to the old one."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benefits import catalogue as cat          # noqa: E402
from benefits import ui                        # noqa: E402

ui.page_setup("Benefits Explorer", "\N{OPEN BOOK}")
ui.hero(
    "\N{OPEN BOOK} Benefits Explorer",
    "What each scheme is, who gets it, when it lands - and what the SG Child "
    "Support Package replaced.",
)

headline = st.columns(4)
headline[0].metric("SG Child Support Package", ui.money(cat.SG_CHILD_SUPPORT_PACKAGE_TOTAL),
                   help="Baby Gift, Child Credits, CDA First Step Grant, CDA "
                        "co-matching and the PSEA top-up.")
headline[1].metric("+ MediSave Grant for Newborns", ui.money(cat.MEDISAVE_GRANT_NEWBORN))
headline[2].metric("+ Edusave contributions", ui.money(cat.EDUSAVE_TOTAL))
headline[3].metric("Total per child", ui.money(cat.HEADLINE_TOTAL),
                   help="Birth to age 17, before any means-tested subsidies.")

tab_all, tab_changed, tab_costs = st.tabs(
    ["Every benefit", "What changed at NDR 2026", "Cost relief and other measures"])

# ---------------------------------------------------------------------------
with tab_all:
    chosen = st.multiselect("Filter by category", cat.CATEGORIES,
                            default=cat.CATEGORIES)
    cards = [c for c in cat.BENEFIT_CARDS if c["category"] in chosen]
    for start in range(0, len(cards), 2):
        row = st.columns(2)
        for col, card in zip(row, cards[start:start + 2]):
            with col:
                st.markdown(
                    f"""<div class="lw-card">
                           {ui.pill(card['category'], cat.CATEGORY_COLOURS[card['category']])}
                           <h4>{card['name']}</h4>
                           <div class="lw-amount">{card['headline']}</div>
                           <div class="lw-meta"><b>When:</b> {card['when']}<br/>
                           <b>Who:</b> {card['who']}<br/>
                           <b>Paid into:</b> {card['vehicle']}</div>
                           <div class="lw-note" style="margin-top:.5rem">{card['detail']}</div>
                        </div>""",
                    unsafe_allow_html=True,
                )
        st.write("")

# ---------------------------------------------------------------------------
with tab_changed:
    st.caption("The Baby Bonus Scheme and the Large Families Scheme are replaced by "
               "the SG Child Support Package. Every Singapore Citizen child now gets "
               "the same level of support, regardless of birth order.")
    mapping = pd.DataFrame(cat.SCHEME_MAPPING)
    category_filter = st.multiselect("Filter by category", cat.CATEGORIES,
                                     default=cat.CATEGORIES, key="mapping_filter")
    mapping = mapping[mapping["Category"].isin(category_filter)]
    st.dataframe(
        mapping[["Category", "Old (Baby Bonus / Large Families Scheme)",
                 "New (SG Child Support Package)", "What changed"]],
        **ui.stretch(), hide_index=True,
    )

    st.markdown("##### Transition rules for children born before 1 Apr 2027")
    st.markdown(
        f"""
- Children still receiving **Baby Bonus Cash Gift** payouts keep them until
  31 Mar 2027, then get a top-up by 30 Apr 2027 that brings the total to
  **{ui.money_md(cat.BABY_GIFT)}**.
- **Child Credits** are backdated. Children who turn 1 to 16 in 2026 receive their
  2026 tranche of {ui.money_md(cat.CHILD_CREDIT_PER_YEAR)} by 30 Apr 2027. Children
  with Jan-Apr birthdays also get their 2027 tranche by then. From 2028 the credits
  arrive on the child's birthday.
- **CDA co-matching caps** for children born between 1 Jan 2015 and 31 Mar 2027 are
  kept until 30 Sep 2027, then move to the uniform
  {ui.money_md(cat.CDA_COMATCH_CAP)} cap from 1 Oct 2027.
- The **PSEA top-up** of {ui.money_md(cat.PSEA_TOP_UP)} goes to children turning 17 from
  2026 onwards; those who turned 17 in 2026 receive it in Jun 2027.
- Discontinued for large families: the extra
  {ui.money_md(cat.LFS_EXTRA_CDA_FSG)} CDA First Step Grant and the
  {ui.money_md(cat.LFS_LIFESG_CREDITS)} Large Family LifeSG Credits for the third and
  later child. The {ui.money_md(cat.LFS_MEDISAVE_GRANT)} Large Family MediSave Grant
  stays, and its extension to large families that have not received it is being
  studied.
        """
    )

# ---------------------------------------------------------------------------
with tab_costs:
    st.caption("These measures cut what families pay rather than paying money out, "
               "so they are deliberately left out of the benefit totals elsewhere in "
               "this app - counting them would double up.")
    for note in cat.COST_RELIEF_NOTES:
        st.markdown(
            f"""<div class="lw-card" style="margin-bottom:.8rem">
                   <h4>{note['name']}</h4>
                   <div class="lw-note">{note['detail']}</div>
                </div>""",
            unsafe_allow_html=True,
        )

st.markdown("---")
ui.sources_block()
ui.disclaimer()
