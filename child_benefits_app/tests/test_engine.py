"""Checks that the projection reproduces the officially announced figures."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from benefits import catalogue as cat
from benefits import engine, leave


def _totals(children, **kwargs):
    frame = engine.project(children, engine.Assumptions(**kwargs))
    return frame.groupby("benefit")["amount"].sum().to_dict(), frame


def test_package_components_sum_to_62k():
    assert cat.SG_CHILD_SUPPORT_PACKAGE_TOTAL == 62_000
    assert cat.CHILD_CREDIT_TOTAL == 32_000
    assert cat.EDUSAVE_TOTAL == 2_540


def test_child_born_under_new_package_gets_about_70k():
    child = engine.Child("New baby", date(2028, 6, 15))
    by_benefit, frame = _totals([child])
    assert by_benefit["Baby Gift"] == 10_000
    assert by_benefit["Child Credits"] == 32_000
    assert by_benefit["CDA First Step Grant"] == 5_000
    assert by_benefit["CDA Co-Matching"] == 5_000
    assert by_benefit["PSEA Top-Up"] == 10_000
    assert by_benefit["MediSave Grant for Newborns"] == 5_000
    assert by_benefit["Edusave Contribution"] == 2_540
    assert frame["amount"].sum() == cat.HEADLINE_TOTAL == 69_540


def test_child_credits_run_from_age_1_to_16():
    child = engine.Child("New baby", date(2028, 6, 15))
    _, frame = _totals([child])
    credits = frame[frame["benefit"] == "Child Credits"]
    assert len(credits) == 16
    assert credits["age"].min() == 1
    assert credits["age"].max() == 16
    assert (credits["amount"] == 2_000).all()


def test_psea_lands_in_the_year_the_child_turns_17():
    child = engine.Child("New baby", date(2028, 6, 15))
    _, frame = _totals([child])
    psea = frame[frame["benefit"] == "PSEA Top-Up"].iloc[0]
    assert psea["year"] == 2045
    assert psea["age"] == 17


def test_existing_child_keeps_only_remaining_child_credits():
    """A child who turns 10 in 2026 gets the 2026-2032 tranches, not all 16."""
    child = engine.Child("Older kid", date(2016, 5, 1))
    _, frame = _totals([child])
    credits = frame[frame["benefit"] == "Child Credits"]
    assert credits["year"].min() == 2026
    assert credits["year"].max() == 2032   # the year the child turns 16
    assert credits["amount"].sum() == 7 * 2_000


def test_baby_bonus_is_topped_up_to_ten_thousand():
    """A child still in the cash-gift window is brought up to $10,000."""
    child = engine.Child("Toddler", date(2024, 8, 1))
    by_benefit, _ = _totals([child])
    total_gift = by_benefit["Baby Bonus Cash Gift"] + by_benefit["Baby Gift top-up"]
    assert total_gift == cat.BABY_GIFT


def test_no_top_up_once_the_cash_gift_window_has_closed():
    child = engine.Child("Older kid", date(2016, 5, 1))
    by_benefit, _ = _totals([child])
    assert "Baby Gift top-up" not in by_benefit


def test_child_born_before_2009_is_outside_the_package():
    child = engine.Child("Teenager", date(2007, 1, 1))
    by_benefit, _ = _totals([child])
    assert "Child Credits" not in by_benefit
    assert "PSEA Top-Up" not in by_benefit


def test_cda_matching_scales_with_the_assumed_saving_rate():
    child = engine.Child("New baby", date(2028, 6, 15))
    half, _ = _totals([child], cda_match_ratio=0.5)
    assert half["CDA Co-Matching"] == 2_500
    none, _ = _totals([child], cda_match_ratio=0.0)
    assert "CDA Co-Matching" not in none


def test_non_citizen_children_are_excluded():
    child = engine.Child("Visitor", date(2028, 6, 15), citizen=False)
    frame = engine.project([child])
    assert frame.empty


def test_birth_order_follows_date_of_birth():
    kids = [
        engine.Child("Third", date(2027, 1, 1)),
        engine.Child("First", date(2020, 1, 1)),
        engine.Child("Second", date(2023, 1, 1)),
    ]
    ordered = engine.order_children(kids)
    assert [c.name for c in ordered] == ["First", "Second", "Third"]
    assert [c.birth_order for c in ordered] == [1, 2, 3]


def test_yearly_summary_reconciles_with_the_grand_total():
    kids = [
        engine.Child("A", date(2019, 3, 4)),
        engine.Child("B", date(2024, 11, 20)),
        engine.Child("C", date(2028, 2, 1)),
    ]
    frame = engine.project(kids)
    pivot = engine.yearly_summary(frame)
    assert round(pivot["Total"].sum(), 2) == round(frame["amount"].sum(), 2)
    per_category = engine.category_totals(frame)
    assert round(sum(per_category.values()), 2) == round(frame["amount"].sum(), 2)


# --- leave -----------------------------------------------------------------

def test_childcare_leave_bands():
    assert leave.childcare_leave_days(1) == 8
    assert leave.childcare_leave_days(2) == 10
    assert leave.childcare_leave_days(3) == 12
    assert leave.childcare_leave_days(5) == 12
    assert leave.childcare_leave_days(0) == 0


def test_three_primary_school_children_go_from_four_to_twenty_four_days():
    """The Government's own worked example from NDR 2026."""
    kids = [
        engine.Child("A", date(2016, 1, 1)),   # turns 13 in 2029, so use 2028
        engine.Child("B", date(2018, 1, 1)),
        engine.Child("C", date(2020, 1, 1)),
    ]
    schedule = leave.childcare_leave_schedule(kids, first_year=2028, last_year=2028)
    row = schedule.iloc[0]
    assert row["Household days (current rules)"] == 4    # 2 days each, youngest is 8
    assert row["Household days (new scheme)"] == 24      # 12 days each


def test_thirty_weeks_of_paid_leave_for_a_child_born_after_april_2026():
    entry = leave.birth_leave([engine.Child("Baby", date(2027, 1, 1))])[0]
    assert (entry.maternity, entry.paternity, entry.shared) == (16, 4, 10)
    assert entry.total == 30


def test_shared_parental_leave_phases_in():
    assert leave.spl_weeks(date(2024, 6, 1)) == 0
    assert leave.spl_weeks(date(2025, 6, 1)) == 6
    assert leave.spl_weeks(date(2026, 6, 1)) == 10
