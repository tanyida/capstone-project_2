# Singapore child benefits

Two ways to explore what the **SG Child Support Package** — announced at the 2026
National Day Rally, replacing the Baby Bonus Scheme and the Large Families Scheme —
is worth to a family, year by year.

| | What it is | How it runs |
| --- | --- | --- |
| [`public/index.html`](public/index.html) | **Little Wins** — a dashboard, calculator, leave tracker and benefit tracker in one page. No server, no build step, no accounts. | Any static host: Vercel, Netlify, Cloudflare Pages, GitHub Pages |
| [`child_benefits_app/`](child_benefits_app/) | The same model as a multi-page **Streamlit** app, with extra reference pages. | Python + Streamlit |

Both are driven by the same benefit rules and produce the same totals.

## What's in the web page

| Section | What it does |
| --- | --- |
| **Overview** | Enter your children; see total benefits, a payout timeline, and a year-by-year table showing each child's school stage, what lands that year and a running total. Open any year for every payout's date, account and status. |
| **Leave tracker** | Log leave as you take it. Childcare and unpaid infant care leave reset each calendar year for each parent; maternity, paternity and Shared Parental Leave are tracked per child against their 12-month window. Add your own leave types (annual leave, sick leave, adoption leave). Flags overruns and leave about to lapse. |
| **Benefit tracker** | Balances for the CDA, LifeSG credits, Edusave, PSEA and MediSave, built from the official schedule plus the deposits and spending you log. Tick off cash payouts as they reach your bank. Warns when LifeSG credits are about to expire and how much CDA saving is still needed to earn the full Government match. |

Tracker data is kept in the visitor's own browser (`localStorage`) and never sent anywhere,
so there are no accounts and nothing to secure on a server. The flip side is that it doesn't
follow people between devices — the **Your data** panel at the bottom of the page downloads or
restores a backup.

The trackers live only in the web page. The Streamlit app forgets everything on refresh, and
giving it per-user storage would mean adding accounts and a database.

## Deploying the web page

The page is one self-contained HTML file. It needs no build, no environment
variables and no backend — visitors just open the URL.

### Vercel

1. Push this repository to GitHub.
2. At [vercel.com/new](https://vercel.com/new), import the repository.
3. Accept the defaults and deploy. [`vercel.json`](vercel.json) already pins the
   framework to none and the output directory to `public/`, so Vercel serves the
   page as-is instead of trying to build the Python app.

You get a public `*.vercel.app` URL, and every push to the branch redeploys.

To deploy from this machine instead, without the GitHub step:

```bash
npx vercel --prod
```

### Other hosts

| Host | What to do |
| --- | --- |
| **Netlify** | Publish directory `public`, build command empty |
| **Cloudflare Pages** | Build output directory `public`, framework preset "None" |
| **GitHub Pages** | Settings → Pages → deploy from branch, folder `/public` (rename to `/docs` if Pages will not offer `/public`) |

Locally, `python -m http.server -d public` serves it at <http://localhost:8000>.

## Editing the page

`web/app.body.html` is the **single source of truth**. It is written in the shape a
Claude Artifact expects — no `<!doctype>`, `<html>`, `<head>` or `<body>` tags,
because the artifact host supplies those.

After editing it, regenerate the deployable file:

```bash
python tools/build_static.py     # web/app.body.html -> public/index.html
```

`tools/build_static.py` adds the document skeleton, the page metadata and the small
CSS reset a static host does not inject. Do not hand-edit `public/index.html` — the
next build overwrites it.

## Running the Streamlit app

```bash
pip install -r child_benefits_app/requirements.txt
streamlit run child_benefits_app/Dashboard.py
```

Streamlit needs a Python server, so it cannot go on Vercel. Free hosting for it is
[Streamlit Community Cloud](https://share.streamlit.io) — also a public URL with no
login for visitors. See [`child_benefits_app/README.md`](child_benefits_app/README.md)
for what each page does.

## Tests

```bash
python -m pytest child_benefits_app/tests -q
```

These pin the projection to the officially announced figures: $62,000 per child from
the package, $32,000 of Child Credits over 16 years, the top-up of existing Baby
Bonus recipients to $10,000, the $500 Child LifeSG Credits for children aged 12 and
below in 2025 and 2026, and the Government's worked example that a couple with three
primary-school children goes from 4 to 24 childcare leave days a year.

The web page ports the same rules to JavaScript. When changing a rule, change it in both
`child_benefits_app/benefits/` and `web/app.body.html`, then check that the same children
give the same total in each — for example Amelia (4 Mar 2019) and Ben (20 Nov 2024) come
to $120,080.

## Disclaimer

A prototype built for educational purposes. Not affiliated with, endorsed by or
operated by any Singapore government agency. Benefit rules are modelled from public
announcements and may be incomplete or out of date — fuller implementation details
are expected in early 2027. Do not rely on it for financial decisions.
