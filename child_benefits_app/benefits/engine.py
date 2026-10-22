"""Turns a list of children into a year-by-year benefit projection."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Iterable

import pandas as pd

from . import catalogue as cat

TODAY = date.today()

# Status flags used to separate money already banked from money still to come.
RECEIVED = "Received"
UPCOMING = "Upcoming"

# Confidence flags, so the user can see which numbers are firm.
CONFIRMED = "Confirmed"
ESTIMATED = "Estimated"
CONDITIONAL = "Conditional"


@dataclass
class Child:
    """A child the user has entered into the calculator."""

    name: str
    dob: date
    birth_order: int = 1
    citizen: bool = True

    @property
    def birth_year(self) -> int:
        return self.dob.year

    def age_on(self, when: date) -> int:
        """Age last birthday on a given date."""
        years = when.year - self.dob.year
        if (when.month, when.day) < (self.dob.month, self.dob.day):
            years -= 1
        return years

    def age_turning_in(self, year: int) -> int:
        """The age the child reaches during the given calendar year."""
        return year - self.dob.year

    @property
    def eligible_for_package(self) -> bool:
        """The package covers children born in, or turning 1 to 17 in, 2026."""
        return self.citizen and self.birth_year >= cat.PACKAGE_FIRST_BIRTH_YEAR


@dataclass
class Line:
    """One payout of one benefit, in one calendar year."""

    child: str
    year: int
    age: int
    benefit: str
    category: str
    vehicle: str
    amount: float
    status: str
    confidence: str
    note: str = ""


@dataclass
class Assumptions:
    """User-tunable inputs that change the projection."""

    cda_match_ratio: float = 1.0        # share of the $5,000 CDA cap actually earned
    include_large_family_medisave: bool = False
    include_edusave: bool = True
    include_medisave_grant: bool = True


def _status(year: int, month: int = 12) -> str:
    """Money is 'received' if its payout date has already passed."""
    if year < TODAY.year:
        return RECEIVED
    if year > TODAY.year:
        return UPCOMING
    return RECEIVED if month <= TODAY.month else UPCOMING


# ---------------------------------------------------------------------------
# Individual benefit rules
# ---------------------------------------------------------------------------

def _baby_gift(child: Child) -> list[Line]:
    """Baby Gift, or the Baby Bonus Cash Gift it replaced."""
    lines: list[Line] = []
    by = child.birth_year

    if child.dob >= cat.BABY_GIFT_START:
        # New regime: $10,000 in two tranches within 12 months of birth.
        tranche = cat.BABY_GIFT / cat.BABY_GIFT_TRANCHES
        second_tranche_year = by if child.dob.month <= 6 else by + 1
        lines.append(Line(
            child.name, by, 0, "Baby Gift", cat.CASH, "Cash to parent", tranche,
            _status(by, child.dob.month), CONFIRMED,
            "First of two tranches, paid shortly after birth.",
        ))
        lines.append(Line(
            child.name, second_tranche_year, second_tranche_year - by,
            "Baby Gift", cat.CASH, "Cash to parent", tranche,
            _status(second_tranche_year), CONFIRMED,
            "Second tranche, paid within 12 months of birth.",
        ))
        return lines

    # Existing children: they were on the Baby Bonus Cash Gift.
    legacy_total = cat.tier_amount(cat.BBCG_TIERS, child.dob, child.birth_order)
    cutoff = date(2027, 3, 31)
    months_old = (cutoff.year - child.dob.year) * 12 + (cutoff.month - child.dob.month) - (cutoff.day < child.dob.day)
    still_in_window = (child.dob >= cat.BBCG_EXTENDED_SCHEDULE_START
                       and months_old < cat.BBCG_LAST_AGE_MONTHS)

    if not still_in_window:
        # The cash gift finished before the package started - no top-up.
        lines.append(Line(
            child.name, by, 0, "Baby Bonus Cash Gift", cat.CASH, "Cash to parent",
            legacy_total, _status(by, child.dob.month), ESTIMATED,
            "Paid in instalments from birth to age 6.5 under the old scheme. "
            "Shown in the birth year as a single figure.",
        ))
        return lines

    # Still receiving payouts: continue until 31 Mar 2027, then top up to $10,000.
    front_loaded = min(cat.BBCG_FRONT_LOADED, legacy_total)
    lines.append(Line(
        child.name, by, 0, "Baby Bonus Cash Gift", cat.CASH, "Cash to parent",
        front_loaded, _status(by, child.dob.month), ESTIMATED,
        "$3,000 at birth plus $1,500 at 6, 12, 15 and 18 months under the old scheme.",
    ))
    top_up = cat.BABY_GIFT - front_loaded
    if top_up > 0:
        lines.append(Line(
            child.name, cat.CATCH_UP_PAYMENT_YEAR,
            child.age_turning_in(cat.CATCH_UP_PAYMENT_YEAR),
            "Baby Gift top-up", cat.CASH, "Cash to parent", top_up,
            UPCOMING, CONFIRMED,
            "Tops the cash gift up to $10,000 in total. Paid by 30 Apr 2027.",
        ))
    return lines


def _child_credits(child: Child) -> list[Line]:
    """$2,000 a year, from the year the child turns 1 to the year they turn 16."""
    lines: list[Line] = []
    for age in range(cat.CHILD_CREDIT_FIRST_AGE, cat.CHILD_CREDIT_LAST_AGE + 1):
        year = child.birth_year + age
        if year < cat.CHILD_CREDIT_FIRST_YEAR:
            # Older children only start from the 2026 tranche.
            continue
        if year <= cat.CATCH_UP_PAYMENT_YEAR:
            note = "Backdated tranche, paid by 30 Apr 2027."
            status = UPCOMING
        else:
            note = "Paid on the child's birthday."
            status = _status(year, child.dob.month)
        lines.append(Line(
            child.name, year, age, "Child Credits", cat.CASH, "Cash to parent",
            cat.CHILD_CREDIT_PER_YEAR, status, CONFIRMED, note,
        ))
    return lines


def _cda(child: Child, assumptions: Assumptions) -> list[Line]:
    """CDA First Step Grant plus government co-matching."""
    lines: list[Line] = []
    by = child.birth_year

    fsg = cat.tier_amount(cat.FSG_TIERS, child.dob, child.birth_order)
    if child.dob >= cat.BABY_GIFT_START:
        fsg = cat.CDA_FIRST_STEP_GRANT  # flat for every birth order under the package
    lines.append(Line(
        child.name, by, 0, "CDA First Step Grant", cat.EDUCATION,
        "Child Development Account", fsg, _status(by, child.dob.month),
        CONFIRMED if child.dob >= cat.BABY_GIFT_START else ESTIMATED,
        "Credited once the Child Development Account is opened.",
    ))

    matched = cat.CDA_COMATCH_CAP * assumptions.cda_match_ratio
    if matched > 0:
        # Spread the assumed co-matching over the preschool years, when most
        # families actually draw on the CDA.
        years = list(range(by, by + cat.CDA_COMATCH_SPREAD_LAST_AGE + 1))
        per_year = matched / len(years)
        for year in years:
            lines.append(Line(
                child.name, year, year - by, "CDA Co-Matching", cat.EDUCATION,
                "Child Development Account", per_year, _status(year), ESTIMATED,
                f"Assumes you save enough to earn {assumptions.cda_match_ratio:.0%} "
                f"of the ${cat.CDA_COMATCH_CAP:,.0f} cap, spread evenly to age "
                f"{cat.CDA_COMATCH_SPREAD_LAST_AGE}. Matching is available until age "
                f"{cat.CDA_COMATCH_LAST_AGE}.",
            ))
    return lines


def _psea(child: Child) -> list[Line]:
    """$10,000 into the PSEA in the year the child turns 17."""
    year = child.birth_year + cat.PSEA_TOP_UP_AGE
    if year < cat.CHILD_CREDIT_FIRST_YEAR:
        return []
    payout_year = max(year, cat.CATCH_UP_PAYMENT_YEAR)
    return [Line(
        child.name, payout_year, cat.PSEA_TOP_UP_AGE, "PSEA Top-Up", cat.EDUCATION,
        "Post-Secondary Education Account", cat.PSEA_TOP_UP,
        _status(payout_year, 6), CONFIRMED,
        "Paid in June of the year the child turns 17.",
    )]


def _medisave_grant(child: Child) -> list[Line]:
    if child.dob >= cat.MEDISAVE_GRANT_NEWBORN_START:
        amount, confidence = cat.MEDISAVE_GRANT_NEWBORN, CONFIRMED
    elif child.dob >= cat.MEDISAVE_GRANT_2023_START:
        amount, confidence = cat.MEDISAVE_GRANT_2023, ESTIMATED
    else:
        amount, confidence = cat.MEDISAVE_GRANT_LEGACY, ESTIMATED
    return [Line(
        child.name, child.birth_year, 0, "MediSave Grant for Newborns",
        cat.HEALTHCARE, "Child's MediSave", amount,
        _status(child.birth_year, child.dob.month), confidence,
        "Pays MediShield Life premiums and recommended childhood vaccinations.",
    )]


def _edusave(child: Child) -> list[Line]:
    lines: list[Line] = []
    schedule = [
        (cat.EDUSAVE_PRIMARY_AGES, cat.EDUSAVE_PRIMARY_PER_YEAR, "Primary school"),
        (cat.EDUSAVE_SECONDARY_AGES, cat.EDUSAVE_SECONDARY_PER_YEAR, "Secondary school"),
    ]
    for (first_age, last_age), amount, label in schedule:
        for age in range(first_age, last_age + 1):
            year = child.birth_year + age
            lines.append(Line(
                child.name, year, age, "Edusave Contribution", cat.EDUCATION,
                "Edusave account", amount, _status(year), ESTIMATED,
                f"{label} annual contribution at current rates.",
            ))
    return lines


def _lifesg_credits(child: Child) -> list[Line]:
    """Child LifeSG Credits, plus Large Family LifeSG Credits for a 3rd+ child.

    Lines sit in the tranche year. A child born in the tranche year is paid the
    following April, which the note records.
    """
    lines: list[Line] = []
    for year, amount in sorted(cat.CHILD_LIFESG_CREDITS.items()):
        age = child.age_turning_in(year)
        if not 0 <= age <= cat.CHILD_LIFESG_MAX_AGE:
            continue
        paid_next_april = age == 0
        lines.append(Line(
            child.name, year, age, "Child LifeSG Credits", cat.CASH, "LifeSG credits",
            amount, _status(year + 1, 4) if paid_next_april else _status(year, 7),
            CONFIRMED,
            "Credited the following April for children born in the tranche year. "
            "Valid for about 12 months." if paid_next_april
            else "Valid for about 12 months from crediting.",
        ))

    if child.birth_order >= cat.LARGE_FAMILY_MIN_CHILDREN:
        first_age, last_age = cat.LARGE_FAMILY_LIFESG_AGES
        for year, amount in sorted(cat.LARGE_FAMILY_LIFESG_CREDITS.items()):
            age = child.age_turning_in(year)
            if not first_age <= age <= last_age:
                continue
            lines.append(Line(
                child.name, year, age, "Large Family LifeSG Credits", cat.CASH,
                "LifeSG credits", amount, _status(year, 9 if year == 2025 else 4),
                CONFIRMED,
                "For a 3rd or later child aged 1 to 6. Ends after the 2026 tranche.",
            ))
    return lines


def _large_family_medisave(children: list[Child]) -> list[Line]:
    """$5,000 MediSave grant around the birth of the 3rd and later children."""
    lines: list[Line] = []
    for child in children:
        if child.birth_order < cat.LARGE_FAMILY_MIN_CHILDREN:
            continue
        lines.append(Line(
            child.name, child.birth_year, 0, "Large Family MediSave Grant",
            cat.HEALTHCARE, "Mother's MediSave", cat.LFS_MEDISAVE_GRANT,
            _status(child.birth_year, child.dob.month), CONDITIONAL,
            "Retained for large families. The Government is studying how to extend "
            "it to large families that have not previously received it.",
        ))
    return lines


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def order_children(children: Iterable[Child]) -> list[Child]:
    """Sort by date of birth and assign birth order."""
    ordered = sorted(children, key=lambda c: c.dob)
    for index, child in enumerate(ordered, start=1):
        child.birth_order = index
    return ordered


def project(children: Iterable[Child], assumptions: Assumptions | None = None) -> pd.DataFrame:
    """Return one row per benefit payout, per child, per calendar year."""
    assumptions = assumptions or Assumptions()
    ordered = order_children(children)
    lines: list[Line] = []

    for child in ordered:
        if not child.citizen:
            continue
        lines += _baby_gift(child)
        lines += _lifesg_credits(child)
        lines += _cda(child, assumptions)
        if child.eligible_for_package:
            lines += _child_credits(child)
            lines += _psea(child)
        if assumptions.include_medisave_grant:
            lines += _medisave_grant(child)
        if assumptions.include_edusave:
            lines += _edusave(child)

    if assumptions.include_large_family_medisave:
        lines += _large_family_medisave([c for c in ordered if c.citizen])

    if not lines:
        return pd.DataFrame(columns=[
            "child", "year", "age", "benefit", "category", "vehicle",
            "amount", "status", "confidence", "note",
        ])

    frame = pd.DataFrame([vars(line) for line in lines])
    return frame.sort_values(["child", "year", "category", "benefit"]).reset_index(drop=True)


def yearly_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Pivot the projection into year x category totals."""
    if frame.empty:
        return pd.DataFrame(columns=["Year"] + cat.CATEGORIES + ["Total"])
    pivot = (
        frame.pivot_table(index="year", columns="category", values="amount",
                          aggfunc="sum", fill_value=0.0)
        .reindex(columns=cat.CATEGORIES, fill_value=0.0)
        .reset_index()
        .rename(columns={"year": "Year"})
    )
    pivot["Total"] = pivot[cat.CATEGORIES].sum(axis=1)
    return pivot


def category_totals(frame: pd.DataFrame) -> dict[str, float]:
    if frame.empty:
        return {c: 0.0 for c in cat.CATEGORIES}
    totals = frame.groupby("category")["amount"].sum().to_dict()
    return {c: float(totals.get(c, 0.0)) for c in cat.CATEGORIES}


def benefit_totals(frame: pd.DataFrame) -> pd.DataFrame:
    """One row per benefit, with the total and the years it spans."""
    if frame.empty:
        return pd.DataFrame(columns=["Benefit", "Category", "Paid into", "Total", "Years"])
    grouped = frame.groupby(["benefit", "category", "vehicle"], as_index=False).agg(
        Total=("amount", "sum"), first_year=("year", "min"), last_year=("year", "max"),
    )
    grouped["Years"] = grouped.apply(
        lambda r: str(int(r.first_year)) if r.first_year == r.last_year
        else f"{int(r.first_year)}-{int(r.last_year)}", axis=1,
    )
    grouped = grouped.rename(columns={
        "benefit": "Benefit", "category": "Category", "vehicle": "Paid into",
    })
    return grouped[["Benefit", "Category", "Paid into", "Total", "Years"]].sort_values(
        "Total", ascending=False).reset_index(drop=True)


def split_by_status(frame: pd.DataFrame) -> tuple[float, float]:
    """Return (already received, still to come)."""
    if frame.empty:
        return 0.0, 0.0
    received = float(frame.loc[frame["status"] == RECEIVED, "amount"].sum())
    upcoming = float(frame.loc[frame["status"] == UPCOMING, "amount"].sum())
    return received, upcoming


def reference_child(birth_year: int | None = None) -> Child:
    """A newborn used for the 'what does any child get' dashboard view."""
    year = birth_year or max(TODAY.year, cat.BABY_GIFT_START.year + 1)
    return Child(name="A child born in %d" % year, dob=date(year, 6, 15))
