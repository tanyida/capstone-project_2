"""Government-paid leave entitlements for working parents.

Two separate things are modelled:

* Leave tied to a **birth** - maternity, paternity, Shared Parental Leave and
  adoption leave. These are one-off entitlements in the child's first year.
* Leave tied to **how many children you have** - childcare leave, which under
  the scheme announced at NDR 2026 scales with the number of Singapore Citizen
  children aged 12 and below.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd

from .engine import Child

# --- Leave tied to a birth -------------------------------------------------

MATERNITY_WEEKS = 16          # Government-Paid Maternity Leave, mother
PATERNITY_WEEKS = 4           # Government-Paid Paternity Leave, mandatory from 1 Apr 2025
ADOPTION_WEEKS = 12           # Government-Paid Adoption Leave

# Shared Parental Leave was phased in.
SPL_PHASES = [
    (date(2026, 4, 1), 10),
    (date(2025, 4, 1), 6),
    (date(1, 1, 1), 0),
]

UNPAID_INFANT_CARE_DAYS = 12  # per parent per year, until the child turns 2

# --- Childcare leave -------------------------------------------------------

# New merged scheme announced at NDR 2026: days per working parent per year,
# by the number of Singapore Citizen children aged 12 and below.
NEW_CCL_BY_CHILD_COUNT = {1: 8, 2: 10}
NEW_CCL_THREE_OR_MORE = 12
NEW_CCL_MAX_AGE = 12

# Current scheme, kept so the two can be compared.
CURRENT_CCL_DAYS = 6          # youngest child aged 6 and below
CURRENT_CCL_MAX_AGE = 6
CURRENT_ECL_DAYS = 2          # youngest child aged 7 to 12
CURRENT_ECL_MAX_AGE = 12

# The start date of the merged scheme has not been announced; implementation
# details were promised for early 2027. This is the app's working assumption.
ASSUMED_NEW_CCL_START_YEAR = 2027


def spl_weeks(dob: date) -> int:
    """Shared Parental Leave weeks for a child with the given date of birth."""
    for start, weeks in SPL_PHASES:
        if dob >= start:
            return weeks
    return 0


@dataclass
class BirthLeave:
    child: str
    year: int
    maternity: int
    paternity: int
    shared: int

    @property
    def total(self) -> int:
        return self.maternity + self.paternity + self.shared


def birth_leave(children: list[Child]) -> list[BirthLeave]:
    """Paid parental leave in each child's first year."""
    return [
        BirthLeave(
            child=c.name,
            year=c.birth_year,
            maternity=MATERNITY_WEEKS,
            paternity=PATERNITY_WEEKS,
            shared=spl_weeks(c.dob),
        )
        for c in sorted(children, key=lambda c: c.dob)
    ]


def childcare_leave_days(children_aged_12_or_below: int, scheme: str = "new") -> int:
    """Childcare leave days per working parent per year."""
    if children_aged_12_or_below <= 0:
        return 0
    if scheme == "new":
        return NEW_CCL_BY_CHILD_COUNT.get(
            children_aged_12_or_below, NEW_CCL_THREE_OR_MORE)
    # Current scheme keys off the age of the youngest child, not the count.
    return CURRENT_CCL_DAYS


def _current_scheme_days(ages: list[int]) -> int:
    """Days per parent under today's CCL / ECL rules, given children's ages."""
    eligible = [a for a in ages if a <= CURRENT_ECL_MAX_AGE]
    if not eligible:
        return 0
    if min(eligible) <= CURRENT_CCL_MAX_AGE:
        return CURRENT_CCL_DAYS
    return CURRENT_ECL_DAYS


def childcare_leave_schedule(
    children: list[Child],
    working_parents: int = 2,
    first_year: int | None = None,
    last_year: int | None = None,
    new_scheme_from: int = ASSUMED_NEW_CCL_START_YEAR,
) -> pd.DataFrame:
    """Year-by-year childcare leave for the household."""
    if not children:
        return pd.DataFrame(columns=[
            "Year", "Children aged 12 and below", "Days per parent (new scheme)",
            "Days per parent (current rules)", "Household days (new scheme)",
            "Household days (current rules)", "Extra days gained",
        ])

    first_year = first_year or min(c.birth_year for c in children)
    last_year = last_year or max(c.birth_year + NEW_CCL_MAX_AGE for c in children)

    rows = []
    for year in range(first_year, last_year + 1):
        ages = [c.age_turning_in(year) for c in children if c.birth_year <= year]
        under_12 = [a for a in ages if a <= NEW_CCL_MAX_AGE]
        if not under_12:
            continue
        new_days = childcare_leave_days(len(under_12), "new") if year >= new_scheme_from \
            else _current_scheme_days(ages)
        current_days = _current_scheme_days(ages)
        rows.append({
            "Year": year,
            "Children aged 12 and below": len(under_12),
            "Days per parent (new scheme)": new_days,
            "Days per parent (current rules)": current_days,
            "Household days (new scheme)": new_days * working_parents,
            "Household days (current rules)": current_days * working_parents,
            "Extra days gained": (new_days - current_days) * working_parents,
        })
    return pd.DataFrame(rows)


def leave_comparison_table() -> pd.DataFrame:
    """How childcare leave changes, by number of young children."""
    rows = []
    for count in (1, 2, 3, 4):
        label = f"{count}+" if count == 4 else str(count)
        new_days = childcare_leave_days(count, "new")
        rows.append({
            "Children aged 12 and below": label if count < 4 else "3 or more",
            "New scheme - days per parent": new_days,
            "New scheme - both parents": new_days * 2,
        })
    # Collapse the 3 and 4 rows, which are the same band.
    table = pd.DataFrame(rows).drop_duplicates(
        subset=["New scheme - days per parent"], keep="first")
    return table.reset_index(drop=True)


def leave_scheme_cards() -> list[dict]:
    """Reference cards for every government-paid leave scheme."""
    return [
        {
            "name": "Government-Paid Maternity Leave",
            "who": "Working mothers of a Singapore Citizen child",
            "amount": f"{MATERNITY_WEEKS} weeks",
            "detail": "The first 8 weeks are employer-paid for the first two children "
                      "and government-paid from the third; the remaining 8 weeks are "
                      "government-paid.",
        },
        {
            "name": "Government-Paid Paternity Leave",
            "who": "Working fathers of a Singapore Citizen child",
            "amount": f"{PATERNITY_WEEKS} weeks",
            "detail": "Mandatory for children born on or after 1 Apr 2025, up from "
                      "2 weeks. Fully government-paid.",
        },
        {
            "name": "Shared Parental Leave",
            "who": "Both parents, shared between them",
            "amount": "10 weeks",
            "detail": "6 weeks for children born on or after 1 Apr 2025, rising to "
                      "10 weeks for children born on or after 1 Apr 2026. Default "
                      "split is half each unless the parents agree otherwise.",
        },
        {
            "name": "Childcare Leave (merged scheme)",
            "who": "Each working parent, every year",
            "amount": "8 to 12 days",
            "detail": "Announced at NDR 2026. Merges today's Childcare Leave and "
                      "Extended Childcare Leave into one scheme that scales with the "
                      "number of Singapore Citizen children aged 12 and below: 8 days "
                      "for one child, 10 for two, 12 for three or more. The start date "
                      "is still to be announced.",
        },
        {
            "name": "Government-Paid Adoption Leave",
            "who": "Adoptive mothers",
            "amount": f"{ADOPTION_WEEKS} weeks",
            "detail": "For adopted children below 12 months old at the point of "
                      "the adoption order application.",
        },
        {
            "name": "Unpaid Infant Care Leave",
            "who": "Each working parent, every year",
            "amount": f"{UNPAID_INFANT_CARE_DAYS} days",
            "detail": "Available in each of the child's first two years. Unpaid, but "
                      "job-protected.",
        },
    ]
