# Iqra — Qur’an & Arabic Learning Centre

Iqra is a proposed Qur’an and Arabic learning centre for children ages 5–12 in Percival Hill, Chattogram. The live website currently supports parent research; it is not an enrollment application.

- **Live website:** [iqra-percival-hill-kickoff.mac-alvi.chatgpt.site](https://iqra-percival-hill-kickoff.mac-alvi.chatgpt.site/)
- **Bengali parent questionnaire:** [Open questionnaire](https://iqra-percival-hill-kickoff.mac-alvi.chatgpt.site/parent-questions)

## Repository contents

- [`dist/client/`](dist/client/) — landing page, interview guide, and Bengali research questionnaire.
- [`dist/server/index.js`](dist/server/index.js) — Worker endpoint that validates and stores questionnaire answers.
- [`drizzle/0000_parent_responses.sql`](drizzle/0000_parent_responses.sql) — D1 table schema.
- [`tests/test_public_site_contract.py`](tests/test_public_site_contract.py) — page and Worker contract tests.
- [`.github/workflows/iqra-contract-tests.yml`](.github/workflows/iqra-contract-tests.yml) — GitHub Actions workflow for the contract tests.

The proposed schedules and fees shown on the site are planning decisions, not final enrollment terms. Parent demand remains under research; do not treat the website as accepting enrollment.

## Run the contract tests

From the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

## Preview the static pages

From the repository root:

```sh
python3 -m http.server 8000 --bind 127.0.0.1 --directory dist/client
```

Open <http://127.0.0.1:8000/>. This preview serves static client files only; it does not run the Worker or connect to D1.

## Deployment and data

The GitHub repository and the live Site’s configured source repository are separate. Changes pushed here do not automatically publish the live website. Deploy only a saved Site version built from its configured source repository.

Questionnaire submissions are intended to remain anonymous. Never use the live form for test submissions: that would write to production D1. Verify Worker persistence with an isolated non-production database and synthetic answers.
