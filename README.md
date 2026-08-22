# ⚙️ BareMetal Match

AI-assisted job hunting for embedded and firmware engineers. Four Claude-powered agents pull real listings, map them against a skills roadmap, write interview prep, and give you resume/LinkedIn strategy — and a separate tracker logs what you actually apply to, so you can see your pipeline at a glance.

## Why this exists

Generic job-search tools don't know the difference between an RTOS scheduler question and a REST API question. BareMetal Match is tuned for embedded work from the ground up — it evaluates listings and builds prep material against a target skill set (default: C, C++, Python, SPI, I2C, RTOS, CAN, J1939), so the output is actually useful for a firmware/embedded search instead of generic advice with the job title swapped in.

## Two tools, one project

**`main.py`** — the AI pipeline. Four agents run in sequence: a job searcher (Adzuna API), a skills advisor, an interview coach, and a career strategist. Each builds on the last agent's output. Takes a few minutes, produces a full markdown report.

**`track.py`** — a lightweight CLI for your own application log. No AI calls, runs instantly. Records every job you apply to with a status (`applied` → `interviewing`/`rejected`/`offer`/`ghosted`/`withdrawn`) and gives you stats: response rate, offer rate, recent activity, top companies.

They're independent — `main.py` finds and prepares you for jobs, `track.py` records what happened when you actually applied.

## Setup

Requires Python 3.10+, [uv](https://docs.astral.sh/uv/getting-started/installation/), an [Anthropic API key](https://console.anthropic.com/), and free [Adzuna API credentials](https://developer.adzuna.com/).

```bash
git clone https://github.com/aniket620/baremetal-match.git
cd baremetal-match
uv sync
cp .env.example .env   # then fill in your three API keys
```

Verify everything's wired up:

```bash
uv run python -c "from src.config import validate_config, print_config; print_config(); print(validate_config())"
```

## Running a search

```bash
uv run main.py
```

Default search is "Embedded Software Engineer" in Los Angeles. To change the role, location, or target skills, edit the top of `main.py`:

```python
JOB_ROLE = "Firmware Engineer"
LOCATION = "Austin, TX"
NUM_RESULTS = 10
TARGET_SKILLS = "C, C++, Rust, SPI, I2C, RTOS, Zephyr"
```

`TARGET_SKILLS` doesn't get sent to the Adzuna search itself (a long exact-match keyword list would return nothing) — it's fed to the skills/interview/career agents so they explicitly evaluate every listing against those skills, even ones the postings don't mention outright.

Output lands in `outputs/`: a combined `job_search_report_[timestamp].md`, plus each agent's individual output for reference.

## Tracking applications

```bash
# Log one
uv run track.py add --title "Embedded Software Engineer" --company "Anduril" \
    --location "Costa Mesa, CA" --url "https://..." --notes "Referred by Jane"

# Move it forward when something happens (use the id printed above)
uv run track.py update a1b2c3d4 --status interviewing

# See everything, or filter
uv run track.py list
uv run track.py list --status interviewing

# Check your numbers
uv run track.py stats
```

`stats` gives you total applications, response rate (% that got any reply — interview, offer, or rejection), offer rate, activity in the last 7/30 days, a pipeline bar chart by status, and your top companies applied to. Data lives in `data/applications.json`, gitignored — it's your history, not project code.

## Project layout

```
baremetal-match/
├── main.py              AI job search pipeline
├── track.py             Application tracker CLI
├── src/
│   ├── config.py        Settings, API keys, paths
│   ├── agents.py        The 4 CrewAI agents
│   ├── tasks.py         Task descriptions for each agent
│   ├── tools.py         Adzuna API integration
│   └── tracker.py       Application tracker logic
├── tests/                Unit tests (pytest)
├── data/                 Your application history (gitignored)
├── outputs/              Generated reports
└── docs/                 Deeper setup/customization/troubleshooting notes
```

## Testing

```bash
uv sync --extra dev
uv run --extra dev pytest -q
```

## Customizing further

Agent personalities and focus areas live in `src/agents.py` (backstories) and `src/tasks.py` (task instructions) — both are plain text you can edit directly. Swap the Claude model in `src/config.py` (`CLAUDE_MODEL`). See `docs/CUSTOMIZATION.md` for a walkthrough of adding a new agent entirely.

## Credits

Built on the multi-agent architecture from "Job Search AI Agent System," created for UC Irvine Claude Builder Club's Intro to AI Agents workshop (October 2025). Reworked into BareMetal Match — embedded-focused search, target-skills evaluation, and the application tracker — by Aniket Londhe.

## License

xxxxxxxxx
