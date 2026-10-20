"""Reference data for Singapore child benefits.

Everything the calculator knows about scheme rules lives here so that the
numbers can be checked against the official sources in one place.

Primary references
------------------
* NDR 2026 - Supporting Families (https://go.gov.sg/ndr2026supportingfamilies,
  which resolves to https://www.madeforfamilies.gov.sg/ndr-2026-supporting-families)
* SG Child Support Package on LifeSG
  (https://www.life.gov.sg/family-parenting/benefits-support/sg-child-support-package)
* CPF Board - Baby Bonus benefits and support for new parents
  (https://www.cpf.gov.sg/member/infohub/educational-resources/
   baby-bonus-benefits-and-support-for-new-parents)
* MOM leave schemes (https://www.mom.gov.sg/employment-practices/leave)
* MOE Edusave (https://www.moe.gov.sg/financial-matters/edusave-account)

All figures are in Singapore dollars.
"""

from __future__ import annotations

from datetime import date

# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------

CASH = "Cash"
EDUCATION = "Education"
HEALTHCARE = "Healthcare"

CATEGORIES = [CASH, EDUCATION, HEALTHCARE]

CATEGORY_COLOURS = {
    CASH: "#2563eb",       # blue
    EDUCATION: "#0d9488",  # teal
    HEALTHCARE: "#d946a0",  # magenta
}

CATEGORY_BLURB = {
    CASH: "Money paid to the parent's bank account and usable for anything.",
    EDUCATION: "Money locked into an education-linked account - CDA, Edusave or PSEA.",
    HEALTHCARE: "Money credited to the child's MediSave account for premiums and care.",
}

# ---------------------------------------------------------------------------
# Key dates for the SG Child Support Package (announced at NDR 2026)
# ---------------------------------------------------------------------------

# Children born on or after this date get the new Baby Gift.
BABY_GIFT_START = date(2027, 4, 1)

# The package was extended to existing children who are born in, or turn
# age 1 to 17 in, 2026. A child turning 17 in 2026 was born in 2009.
PACKAGE_FIRST_BIRTH_YEAR = 2009

# Child Credits are backdated to 2026; the 2026 tranche is paid by 30 Apr 2027.
CHILD_CREDIT_FIRST_YEAR = 2026
CATCH_UP_PAYMENT_YEAR = 2027

# ---------------------------------------------------------------------------
# SG Child Support Package - component amounts
# ---------------------------------------------------------------------------

BABY_GIFT = 10_000            # cash, 2 tranches within 12 months of birth
BABY_GIFT_TRANCHES = 2

CHILD_CREDIT_PER_YEAR = 2_000  # cash, each year the child turns 1 to 16
CHILD_CREDIT_FIRST_AGE = 1
CHILD_CREDIT_LAST_AGE = 16
CHILD_CREDIT_TOTAL = CHILD_CREDIT_PER_YEAR * (
    CHILD_CREDIT_LAST_AGE - CHILD_CREDIT_FIRST_AGE + 1
)  # $32,000

CDA_FIRST_STEP_GRANT = 5_000   # into the Child Development Account at birth
CDA_COMATCH_CAP = 5_000        # uniform cap from 1 Oct 2027, until the child turns 12
CDA_COMATCH_LAST_AGE = 12
CDA_COMATCH_SPREAD_LAST_AGE = 6  # assumption: most CDA saving happens by age 6

PSEA_TOP_UP = 10_000           # into the PSEA in June of the year the child turns 17
PSEA_TOP_UP_AGE = 17

SG_CHILD_SUPPORT_PACKAGE_TOTAL = (
    BABY_GIFT + CHILD_CREDIT_TOTAL + CDA_FIRST_STEP_GRANT
    + CDA_COMATCH_CAP + PSEA_TOP_UP
)  # $62,000

# ---------------------------------------------------------------------------
# Benefits that sit outside the package but still land in the same wallet
# ---------------------------------------------------------------------------

MEDISAVE_GRANT_NEWBORN = 5_000          # born on or after 1 Apr 2025
MEDISAVE_GRANT_NEWBORN_START = date(2025, 4, 1)
MEDISAVE_GRANT_2023 = 4_000             # born 1 Jan 2023 - 31 Mar 2025
MEDISAVE_GRANT_2023_START = date(2023, 1, 1)
MEDISAVE_GRANT_LEGACY = 3_000           # born before 1 Jan 2023

EDUSAVE_PRIMARY_PER_YEAR = 230          # years the child turns 7 to 12
EDUSAVE_SECONDARY_PER_YEAR = 290        # years the child turns 13 to 16
EDUSAVE_PRIMARY_AGES = (7, 12)
EDUSAVE_SECONDARY_AGES = (13, 16)
EDUSAVE_TOTAL = (
    EDUSAVE_PRIMARY_PER_YEAR * 6 + EDUSAVE_SECONDARY_PER_YEAR * 4
)  # $2,540

# $62,000 + $5,000 MediSave + ~$2,540 Edusave = about $70,000 per child.
HEADLINE_TOTAL = (
    SG_CHILD_SUPPORT_PACKAGE_TOTAL + MEDISAVE_GRANT_NEWBORN + EDUSAVE_TOTAL
)

# ---------------------------------------------------------------------------
# Legacy scheme amounts, used to reconstruct what older children already got
# ---------------------------------------------------------------------------

# Baby Bonus Cash Gift by cohort -> (1st/2nd child, 3rd and subsequent child)
BBCG_TIERS = [
    (date(2023, 2, 14), (11_000, 13_000)),
    (date(2015, 1, 1), (8_000, 10_000)),
    (date(1, 1, 1), (6_000, 8_000)),
]

# The cash gift is paid out from birth until the child turns 6.5.
BBCG_LAST_AGE = 6.5
BBCG_FRONT_LOADED = 9_000  # $3,000 at birth + $1,500 at 6, 12, 15 and 18 months

# CDA First Step Grant by cohort.
FSG_TIERS = [
    (date(2025, 2, 18), (5_000, 10_000)),   # 3rd+ got $10,000 - now discontinued
    (date(2023, 2, 14), (5_000, 5_000)),
    (date(1, 1, 1), (3_000, 3_000)),
]

# Large Families Scheme (being replaced by the SG Child Support Package).
LFS_LIFESG_CREDITS = 6_000       # discontinued
LFS_EXTRA_CDA_FSG = 5_000        # discontinued
LFS_MEDISAVE_GRANT = 5_000       # retained; extension to other large families under study
LARGE_FAMILY_MIN_CHILDREN = 3

# LifeSG credits - spendable at merchants that accept PayNow UEN QR or NETS QR,
# credited to the CDA trustee's LifeSG app and valid for about 12 months.
# Keyed by the tranche year. No tranches beyond 2026 have been announced.
CHILD_LIFESG_CREDITS = {2025: 500, 2026: 500}   # each SC child aged 0 to 12
CHILD_LIFESG_MAX_AGE = 12
LARGE_FAMILY_LIFESG_CREDITS = {2025: 1_000, 2026: 1_000}  # each 3rd+ child aged 1 to 6
LARGE_FAMILY_LIFESG_AGES = (1, 6)

# ---------------------------------------------------------------------------
# Old scheme -> new scheme mapping (for the "What changed" view)
# ---------------------------------------------------------------------------

SCHEME_MAPPING = [
    {
        "Old (Baby Bonus / Large Families Scheme)": "Baby Bonus Cash Gift - $11,000 (1st/2nd child) or $13,000 (3rd+), paid in instalments until age 6.5",
        "New (SG Child Support Package)": "Baby Gift - $10,000 cash for every child, paid in 2 tranches within 12 months of birth",
        "What changed": "Same amount for every birth order, and paid out far earlier when costs are highest.",
        "Category": CASH,
    },
    {
        "Old (Baby Bonus / Large Families Scheme)": "No equivalent - cash support stopped at age 6.5",
        "New (SG Child Support Package)": "Child Credits - $2,000 a year for 16 years (the year the child turns 1 to 16), $32,000 in total",
        "What changed": "Brand new. Cash support now runs the whole way through school.",
        "Category": CASH,
    },
    {
        "Old (Baby Bonus / Large Families Scheme)": "CDA First Step Grant - $5,000, plus $5,000 more for the 3rd+ child under the Large Families Scheme",
        "New (SG Child Support Package)": "CDA First Step Grant - $5,000 for every child",
        "What changed": "The large-family top-up is discontinued; the base grant is unchanged.",
        "Category": EDUCATION,
    },
    {
        "Old (Baby Bonus / Large Families Scheme)": "CDA government co-matching capped at $4,000 (1st), $7,000 (2nd), $9,000 (3rd/4th), $15,000 (5th+)",
        "New (SG Child Support Package)": "CDA co-matching capped at a uniform $5,000 for every child",
        "What changed": "One cap for everyone. Existing caps are kept until 30 Sep 2027, then move to $5,000 from 1 Oct 2027.",
        "Category": EDUCATION,
    },
    {
        "Old (Baby Bonus / Large Families Scheme)": "No equivalent",
        "New (SG Child Support Package)": "PSEA top-up - $10,000 in June of the year the child turns 17",
        "What changed": "Brand new. Aimed at post-secondary and tertiary fees.",
        "Category": EDUCATION,
    },
    {
        "Old (Baby Bonus / Large Families Scheme)": "Large Family LifeSG Credits - $1,000 a year for each 3rd+ child aged 1 to 6",
        "New (SG Child Support Package)": "Discontinued after the 2026 tranche - folded into the flat per-child support",
        "What changed": "No disbursements from 2027, but every child now gets $32,000 in Child Credits regardless of birth order.",
        "Category": CASH,
    },
    {
        "Old (Baby Bonus / Large Families Scheme)": "Large Family MediSave Grant - $5,000 for the 3rd+ child",
        "New (SG Child Support Package)": "Retained; the Government is studying how to extend it to large families that have not received it",
        "What changed": "Kept in place for large families.",
        "Category": HEALTHCARE,
    },
    {
        "Old (Baby Bonus / Large Families Scheme)": "MediSave Grant for Newborns - $5,000 (unchanged, outside the package)",
        "New (SG Child Support Package)": "MediSave Grant for Newborns - $5,000",
        "What changed": "No change. Sits on top of the $62,000 package.",
        "Category": HEALTHCARE,
    },
    {
        "Old (Baby Bonus / Large Families Scheme)": "Edusave - $230 a year in primary school, $290 a year in secondary school (unchanged, outside the package)",
        "New (SG Child Support Package)": "Edusave - $230 / $290 a year",
        "What changed": "No change. Sits on top of the $62,000 package.",
        "Category": EDUCATION,
    },
]

# ---------------------------------------------------------------------------
# Benefit definitions used by the explorer view
# ---------------------------------------------------------------------------

BENEFIT_CARDS = [
    {
        "name": "Baby Gift",
        "category": CASH,
        "vehicle": "Cash to parent",
        "headline": "$10,000",
        "when": "2 tranches within 12 months of birth",
        "who": "Every Singapore Citizen child born on or after 1 Apr 2027. Children born earlier who are still receiving Baby Bonus Cash Gift payouts are topped up to $10,000 by 30 Apr 2027.",
        "detail": "Replaces the Baby Bonus Cash Gift. The same amount goes to every child, no matter the birth order, and it arrives in the first year instead of being stretched to age 6.5.",
    },
    {
        "name": "Child Credits",
        "category": CASH,
        "vehicle": "Cash to parent",
        "headline": "$32,000",
        "when": "$2,000 a year, from the year the child turns 1 to the year they turn 16",
        "who": "Every Singapore Citizen child. Payouts start Apr 2027 and land on the child's birthday from 2028.",
        "detail": "The single largest component of the package and completely new. The 2026 tranche, and the 2027 tranche for children with Jan-Apr birthdays, are both paid by 30 Apr 2027.",
    },
    {
        "name": "CDA First Step Grant",
        "category": EDUCATION,
        "vehicle": "Child Development Account",
        "headline": "$5,000",
        "when": "Once the CDA is opened, shortly after birth",
        "who": "Every Singapore Citizen child, regardless of birth order.",
        "detail": "Spendable at Baby Bonus Approved Institutions - childcare and infant care centres, kindergartens, clinics, hospitals, pharmacies and optical shops.",
    },
    {
        "name": "CDA Government Co-Matching",
        "category": EDUCATION,
        "vehicle": "Child Development Account",
        "headline": "Up to $5,000",
        "when": "Dollar-for-dollar as you save, until the child turns 12",
        "who": "Every Singapore Citizen child. A uniform $5,000 cap applies from 1 Oct 2027.",
        "detail": "This is the one benefit you have to act on - the Government only matches what you actually deposit. Existing birth-order caps are honoured until 30 Sep 2027.",
    },
    {
        "name": "PSEA Top-Up",
        "category": EDUCATION,
        "vehicle": "Post-Secondary Education Account",
        "headline": "$10,000",
        "when": "June of the year the child turns 17",
        "who": "Every Singapore Citizen child. Children who turned 17 in 2026 receive it in Jun 2027.",
        "detail": "Meant for polytechnic, ITE, junior college and university costs. Unused PSEA balances can later be transferred to siblings.",
    },
    {
        "name": "MediSave Grant for Newborns",
        "category": HEALTHCARE,
        "vehicle": "Child's MediSave account",
        "headline": "$5,000",
        "when": "At birth",
        "who": "Every Singapore Citizen child born on or after 1 Apr 2025 (raised from $4,000).",
        "detail": "Pays MediShield Life premiums, recommended childhood vaccinations and approved outpatient treatments. Sits outside the $62,000 package.",
    },
    {
        "name": "Edusave Contributions",
        "category": EDUCATION,
        "vehicle": "Edusave account",
        "headline": "$2,540 in total",
        "when": "$230 a year from age 7 to 12, $290 a year from age 13 to 16",
        "who": "Every Singapore Citizen child of school-going age.",
        "detail": "Pays for enrichment programmes, second-tier miscellaneous fees and school activities. Sits outside the $62,000 package.",
    },
    {
        "name": "Child LifeSG Credits",
        "category": CASH,
        "vehicle": "LifeSG credits",
        "headline": "$500 a year",
        "when": "2025 and 2026 tranches; valid about 12 months from crediting",
        "who": "Every Singapore Citizen child aged 0 to 12 in the tranche year. Credited to the CDA trustee's LifeSG app; children born in the tranche year receive it the following April.",
        "detail": "Spend at merchants that accept PayNow UEN QR or NETS QR. Unused credits expire and cannot be carried forward - the 2025 tranche expired on 6 Jul 2026.",
    },
    {
        "name": "Large Family MediSave Grant",
        "category": HEALTHCARE,
        "vehicle": "Mother's MediSave account",
        "headline": "$5,000",
        "when": "Around the birth of the 3rd and subsequent child",
        "who": "Families with 3 or more children. The Government is studying how to extend it to large families that have not received it.",
        "detail": "One of the few large-family benefits kept when the Large Families Scheme was folded into the SG Child Support Package.",
    },
]

# Measures that change household costs rather than paying money out. These are
# deliberately kept out of the benefit totals so nothing is double counted.
COST_RELIEF_NOTES = [
    {
        "name": "Cheaper full-day childcare",
        "detail": "Fees at government-supported preschools fall to $150 a month for full-day childcare and $300 for infant care, before means-tested subsidies. Rolled out progressively from 2028, reaching those levels by 2030, for every Singaporean child regardless of household income.",
    },
    {
        "name": "Extra HDB ballot chance",
        "detail": "From Feb 2027, first-timer families with, or expecting, children get one additional ballot chance for each Singapore Citizen child aged 18 and below.",
    },
    {
        "name": "Employer leave costs covered",
        "detail": "The Government covers the cost of all child-related leave - maternity, paternity, adoption, Shared Parental Leave and childcare leave - for all birth orders, up to the reimbursement cap.",
    },
]

SOURCES = [
    ("NDR 2026 - Supporting Families", "https://go.gov.sg/ndr2026supportingfamilies"),
    ("SG Child Support Package (LifeSG)", "https://www.life.gov.sg/family-parenting/benefits-support/sg-child-support-package"),
    ("CPF - Baby Bonus benefits and support for new parents", "https://www.cpf.gov.sg/member/infohub/educational-resources/baby-bonus-benefits-and-support-for-new-parents"),
    ("MSF - Marriage & Parenthood measures at NDR 2026", "https://www.population.gov.sg/marriage-parenthood-measures-at-national-day-rally-2026/"),
    ("MOM - Leave schemes", "https://www.mom.gov.sg/employment-practices/leave"),
    ("MOE - Edusave Account", "https://www.moe.gov.sg/financial-matters/edusave-account"),
]

DISCLAIMER = """
**IMPORTANT NOTICE:** This web application is a prototype developed for educational
purposes only. The information provided here is **not** intended for real-world usage
and should not be relied upon for making any decisions, especially those related to
financial, legal or healthcare matters.

Benefit rules are modelled from public announcements and may be incomplete or out of
date - the Government has said fuller implementation details will be shared in early
2027. Always check the official sources and consult qualified professionals for
accurate and personalised advice.
"""


def tier_amount(tiers, dob: date, birth_order: int) -> int:
    """Return the cohort amount for a date of birth and birth order.

    ``tiers`` is a list of ``(effective_from, (first_second, third_plus))``
    ordered from newest to oldest.
    """
    for start, (first_second, third_plus) in tiers:
        if dob >= start:
            return third_plus if birth_order >= 3 else first_second
    return tiers[-1][1][0]
