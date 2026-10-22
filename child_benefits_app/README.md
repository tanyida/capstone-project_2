# ParentedSG - Singapore child benefits dashboard (Streamlit)

A Streamlit app that shows parents every government benefit their child is
entitled to, year by year, from birth to age 17 - and lets them calculate the
total for their own children.

Built around the **SG Child Support Package** announced at the 2026 National Day
Rally, which replaces the Baby Bonus Scheme and the Large Families Scheme.

## Running it

```bash
pip install -r child_benefits_app/requirements.txt
streamlit run child_benefits_app/Dashboard.py
```

The app has no external services and needs no API keys or secrets.

## Pages

| Page | What it does |
| --- | --- |
| **Dashboard** (`Dashboard.py`) | One-glance view: total projected benefits, a stacked bar of every calendar year split by cash / education / healthcare, a cumulative curve, the full benefit list and a leave snapshot. Shows the standard picture for one child until you add your own. |
| **Benefits Calculator** | Enter each child's name and date of birth, then get the total projected benefits broken down by year, by child, by benefit and payout by payout, with a CSV download. |
| **Parental Leave** | Government-paid leave, including the merged childcare leave scheme that scales with the number of children aged 12 and below, plus a year-by-year household schedule and the paid leave available at each birth. |
| **Benefits Explorer** | Reference cards for every scheme, a side-by-side map of the old Baby Bonus / Large Families benefits against the new package, the transition rules, and the cost-relief measures kept out of the totals. |
| **Methodology** | How the projection is built, every assumption it makes, the confidence flags and the sources. |

## What a child receives

| Component | Amount | When | Category |
| --- | --- | --- | --- |
| Baby Gift | $10,000 | 2 tranches within 12 months of birth | Cash |
| Child Credits | $32,000 | $2,000 a year, the year the child turns 1 to 16 | Cash |
| CDA First Step Grant | $5,000 | On opening the CDA | Education |
| CDA government co-matching | up to $5,000 | Dollar-for-dollar as you save, until age 12 | Education |
| PSEA top-up | $10,000 | June of the year the child turns 17 | Education |
| **SG Child Support Package** | **$62,000** | | |
| MediSave Grant for Newborns | $5,000 | At birth | Healthcare |
| Edusave contributions | $2,540 | $230 a year ages 7-12, $290 ages 13-16 | Education |
| **Total per child** | **$69,540** | Birth to age 17 | |

Childcare leave under the merged scheme: **8 days** per working parent per year
for one child aged 12 and below, **10 days** for two, **12 days** for three or
more. Paid leave in the child's first year: 16 weeks maternity + 4 weeks
paternity + 10 weeks Shared Parental Leave = **30 weeks** for the couple.

## Layout

```
child_benefits_app/
├── Dashboard.py                       # dashboard and entry point
├── benefits/
│   ├── catalogue.py             # every scheme rule, amount and date - the single source of truth
│   ├── engine.py                # turns children into a year-by-year projection
│   ├── leave.py                 # leave entitlements
│   └── ui.py                    # styling, the child editor and the charts
├── pages/                       # Streamlit multipage app
└── tests/test_engine.py         # pins the projection to the announced figures
```

All scheme rules live in `benefits/catalogue.py`, so updating an amount when the
implementation details are published in 2027 is a one-line change.

## Tests

```bash
python -m pytest child_benefits_app/tests -q
```

The tests check the projection against the officially announced figures: $62,000
per child from the package, $32,000 of Child Credits over 16 years, the top-up of
existing Baby Bonus recipients to $10,000, and the Government's own worked
example that a couple with three primary-school children goes from 4 to 24
childcare leave days a year.

## Sources

- [NDR 2026 - Supporting Families](https://go.gov.sg/ndr2026supportingfamilies)
- [SG Child Support Package (LifeSG)](https://www.life.gov.sg/family-parenting/benefits-support/sg-child-support-package)
- [CPF - Baby Bonus benefits and support for new parents](https://www.cpf.gov.sg/member/infohub/educational-resources/baby-bonus-benefits-and-support-for-new-parents)
- [MSF - Marriage & Parenthood measures at NDR 2026](https://www.population.gov.sg/marriage-parenthood-measures-at-national-day-rally-2026/)
- [MOM - Leave schemes](https://www.mom.gov.sg/employment-practices/leave)
- [MOE - Edusave Account](https://www.moe.gov.sg/financial-matters/edusave-account)

## Disclaimer

This web application is a prototype developed for educational purposes only. The
information provided here is **not** intended for real-world usage and should not
be relied upon for making any decisions, especially those related to financial,
legal or healthcare matters. Benefit rules are modelled from public
announcements and may be incomplete or out of date - the Government has said
fuller implementation details will be shared in early 2027. Always check the
official sources and consult qualified professionals for accurate and
personalised advice.
