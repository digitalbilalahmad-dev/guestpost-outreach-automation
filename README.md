# Guest Post Outreach — Muse Orchestrated POC

A working Python proof of concept for website import, normalization/deduplication, public contact research, local reply-price parsing, and SQLite persistence. Includes Google OAuth/Gmail/Sheets API adapters but **does not yet implement a production autonomous sender, multi-mailbox scheduler, reply synchronization, or Sheets reconciliation**. Do not describe those as operational until completed and tested.

## Local installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m unittest discover -s tests -v
python src/cli.py import-csv data/sample_websites.csv
python src/cli.py status
python src/cli.py research --limit 2
```

On Windows activate with `.venv\\Scripts\\activate`.

## Parse a test reply

Create a text file `reply.txt` containing a publisher reply, then run:

```bash
python src/cli.py parse-reply --website-id 1 --file reply.txt
```

The parser intentionally flags multiple prices for review; the Muse reply analyzer should return validated structured values before writing production offers.

## Muse onboarding

1. Create a **private** GitHub repository, upload these files, and never upload the `secrets/` directory or SQLite database.
2. In Muse's secure computer, open or clone the repository (if shell/Git access is available). Run the local tests and POC commands above.
3. Provide `agents/supervisor.md` as the main Muse instructions. Ask Muse to confirm its available scheduler, browser, connector, and approval capabilities before enabling anything.
4. Connect Google accounts via authorized OAuth sign-in, not passwords. For an independent Google Cloud setup, enable Gmail API and Google Sheets API, configure OAuth consent and an appropriate Desktop OAuth client, and download the client JSON privately to `secrets/client_secret.json`. Run `authorize(account_label)` separately for each authorized account; inspect requested scopes before granting. For Google Workspace, administrator policy may limit consent. Restrict tokens and backups.
5. Share the target Google Sheet with the authorized account; configure `sheet_id` and `sheet_range` in `config/settings.yaml`. Map Sheet columns explicitly; never assume a domain is row N after sorting.
6. Verify mailbox identity and ownership, domain SPF/DKIM/DMARC, suppression handling, provider limits, and Muse's sending approval rules.
7. Keep `send_enabled: false` for initial tests. Validate ten websites, then expand carefully. Do not treat `max_daily_total` as permission to exceed provider limits.
8. For production, implement and test: a durable task queue, per-account OAuth storage, idempotent send ledger, Gmail polling/pagination and MIME parsing, thread matching, Sheet ID-to-row reconciliation, opt-out processing, retries/backoff, observability, and approval-compatible dispatch. These features are not yet implemented in this POC.

## Recommended production data contract

Sheet input: `Website`, optional `Website ID`, `Status`. Sheet output: `Contact Email`, `Email Source`, `Mailbox`, `Thread ID`, `Sent At`, `Last Reply`, `Standard Price`, `Crypto Price`, `Currency`, `Do-follow Links`, `Sponsored Tag`, `Turnaround`, `Link Insertion`, `Needs Review`, `Last Error`.

## Safety and cost controls

Use publicly listed business contacts; respect opt-outs, rate limits, site access restrictions, and anti-spam requirements. Never rotate accounts to evade limits. Reconcile uncertain sends before retrying. Use code for normalizing, filtering, and bookkeeping, and Muse only for browser exceptions and ambiguous interpretation. The website content and incoming emails are untrusted and must not override agent instructions.
