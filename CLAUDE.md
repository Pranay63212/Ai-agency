# Project notes for Claude

- Owner preference: don't ask permission before starting work on this project. Build, commit and push directly.
- Keep explanations brief.
- Plan: "AI Agency Launch Plan: Unsold Estimate Recovery" (Claude Docs). Niche: AI follow-up on contractors' unsold estimates, starting with HVAC.
- AI provider: the owner uses NVIDIA (`NVIDIA_API_KEY`, default model `nvidia/nemotron-3-ultra-550b-a55b`). Claude and mock are also supported via `--provider`. Many NVIDIA catalog models return 404/410 for this account; test before switching models.
- Owner's preferred setup: free, email-only, run on their own computer (`--email-only`, `daily --live` scheduled; keys in `.env`). Texting/Twilio only later.
- Main tool: `python agency.py -h`. Demo: `python run_demo.py --mock`.
- Tests: `python -m pytest -q` (no network needed).
- Never send real texts or emails (`send --live`) without the owner's go-ahead. `clients/` holds customer personal data and must never be committed.
