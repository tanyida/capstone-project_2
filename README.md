# ParentedSG

Every Singapore government benefit your children are entitled to under the **SG Child Support
Package**, and the leave you take as parents — tracked together in one family account.

| | What it is | How it runs |
| --- | --- | --- |
| [`public/`](public/) | **ParentedSG** — the web app: overview, leave tracker, benefit tracker, sign-in and shared family accounts. | Any static host (Vercel, Netlify, Cloudflare Pages). Family accounts use Supabase. |
| [`child_benefits_app/`](child_benefits_app/) | The same benefit rules as a **Streamlit** app with reference pages. | Python + Streamlit |

Both share the same benefit rules and give the same totals.

## What's in the web app

| Section | What it does |
| --- | --- |
| **Sign in** | Each parent signs in with their own email and password. One starts a family account; the other joins it with an invite code. Both then see and update the same records. |
| **Overview** | Built only from the children you add. Total entitlement from birth to 17, what's been received, the balance left in each account and what's still to come — plus each parent's leave left this year. Updates as either parent logs leave or spending. |
| **Leave tracker** | Childcare and unpaid infant care leave per parent, reset every calendar year. Maternity, paternity and Shared Parental Leave only for children within 12 months of birth (or expected) — once a child's window closes, that leave no longer applies. Custom leave types (annual, sick, adoption). Dates are entered as DD/MM/YYYY. |
| **Benefit tracker** | Balances for the CDA, LifeSG credits, Edusave, PSEA and MediSave from the official schedule plus logged deposits and spending. Tick off cash payouts as they arrive. Warnings for LifeSG credits about to expire and CDA match still to earn. |

People who'd rather not make an account can choose **Use ParentedSG on this device only** on the
sign-in page; their records then stay in that browser.

## Deploying

The site is static — no build step. On Vercel, import the repository and deploy;
[`vercel.json`](vercel.json) serves the `public/` folder as-is. Without family accounts switched
on, the site still works in device-only mode.

### Turning on family accounts

Family accounts use [Supabase](https://supabase.com) for sign-in and the shared database. The free
plan is enough to start.

1. **Create a project** at supabase.com.
2. **Create the tables.** In the dashboard open *SQL Editor → New query*, paste the whole of
   [`supabase/schema.sql`](supabase/schema.sql) and press *Run*. It is safe to run again.
3. **Tell Supabase where the site lives.** Under *Authentication → URL Configuration*, set the
   *Site URL* to your site's address (for example `https://parentedsg.vercel.app`) and add the same
   address under *Redirect URLs*. Confirmation and password-reset emails link back to it.
4. **Connect the site.** Under *Project Settings → API*, copy the *Project URL* and the *anon public*
   key into [`public/config.js`](public/config.js). The anon key is designed to be public — the
   row-level security created in step 2 is what keeps each family's records private.
5. **Deploy** — commit and push; Vercel redeploys.

Then create an account on the site, choose **Start family account**, and give your spouse the
invite code shown on the Overview. A family holds at most two parents.

Things to know before real families rely on it:

- Supabase's built-in email sender is rate-limited and meant for testing. For real users, connect
  your own email provider under *Authentication → Emails → SMTP settings*.
- Free projects are paused after a period of inactivity; check Supabase's current plan limits.
- Each family's records live in your Supabase project. You are responsible for that data — take
  Supabase backups and consider what privacy notice your users need.

### How the data is protected

- Every table has row-level security: a signed-in parent can read and change only rows belonging to
  a family they are a member of. The public key on its own can read nothing.
- Joining a family, leaving it and changing its invite code only happen through database functions
  that check who is calling. Nobody can add themselves to a family directly, see another family's
  invite code, or point a record at another family's child.
- Restoring a backup replaces the family's records in a single transaction — it applies in full or
  not at all.

## Editing the page

`web/app.body.html` is the single source of truth for the page. After editing it, regenerate the
deployable file:

```bash
python tools/build_static.py     # web/app.body.html -> public/index.html
```

The build adds the document `<head>`, the sign-in library
([`public/vendor/supabase-js-2.118.0.js`](public/vendor/), served from the site rather than a CDN)
and `config.js`. Don't hand-edit `public/index.html` — the next build overwrites it.

## Running the Streamlit app

```bash
pip install -r child_benefits_app/requirements.txt
streamlit run child_benefits_app/Dashboard.py
```

Streamlit needs a Python server, so it can't go on Vercel; [Streamlit Community
Cloud](https://share.streamlit.io) hosts it for free. It has no accounts or trackers.

## Tests

```bash
python -m pytest child_benefits_app/tests -q
```

These pin the benefit rules to the announced figures: $62,000 per child from the package, $32,000
of Child Credits over 16 years, Baby Bonus recipients still being paid topped up to $10,000, the
$500 Child LifeSG Credits for children aged 12 and below in 2025 and 2026, and the Government's
worked example that a couple with three primary-school children goes from 4 to 24 childcare leave
days a year.

The web page ports the same rules to JavaScript. When changing a rule, change it in both
`child_benefits_app/benefits/` and `web/app.body.html`, and check the same children give the same
total in each — for example Amelia (04/03/2019) and Ben (20/11/2024) come to $120,080.

## Disclaimer

A prototype built for educational purposes. Not affiliated with, endorsed by or operated by any
Singapore government agency. Benefit and leave rules are modelled from public announcements and may
be incomplete or out of date. Do not rely on it for financial decisions.
