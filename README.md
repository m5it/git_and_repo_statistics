# GitHub Analytics Scripts

A small collection of Python scripts for tracking GitHub repository metrics over time.

## Scripts

### 1. `collect_github_traffic.py`

Collects **private traffic data** (clones and views) for repositories you own or have push access to.

**Works only for your own repos** because GitHub restricts clone/view traffic data to users with push access.

#### Usage

```bash
GITHUB_TOKEN=your_token python3 collect_github_traffic.py [username]
```

If `username` is omitted, defaults to `m5it`.

#### Outputs

- `traffic_reports/traffic_YYYY-MM-DD.txt` — human-readable daily report

#### Example

```bash
GITHUB_TOKEN=ghp_xxx python3 collect_github_traffic.py m5it
```

#### Cron job (daily at 09:00)

```bash
0 9 * * * cd /path/to/this/dir && GITHUB_TOKEN=ghp_xxx python3 collect_github_traffic.py m5it >> cron.log 2>&1
```

---

### 2. `collect_github_popularity.py`

Collects **public popularity stats** (stars, forks, watchers, open issues) for any public GitHub user. Useful for competitive analysis and tracking project popularity over time.

#### Usage

**Single user:**

```bash
GITHUB_TOKEN=your_token python3 collect_github_popularity.py username
```

**Batch mode from a list file:**

```bash
GITHUB_TOKEN=your_token python3 collect_github_popularity.py -l users.txt
```

#### Outputs

- `popularity_reports/popularity_USERNAME_YYYY-MM-DD.txt` — human-readable daily report
- `popularity_reports/history_USERNAME.csv` — time-series data for graphing

#### Token sources (checked in order)

1. `GITHUB_TOKEN` environment variable
2. `~/.github_token` file
3. `.env` file with `GITHUB_TOKEN=...`

#### Example list file (`users.txt`)

```text
# Lines starting with # are ignored
# You can also add comments after the username

m5it
yumiaura
electerm
```

#### Example: track SSH client competitors

```bash
cat > ssh_competitors.txt <<EOF
electerm
kingToolbox
tabbyml
PowerShell
openssh
EOF

GITHUB_TOKEN=ghp_xxx python3 collect_github_popularity.py -l ssh_competitors.txt
```

---

## CSV History Format

`history_USERNAME.csv` contains one row per repo per day:

```csv
date,repo,url,stars,forks,watchers,issues,language,updated
2026-07-28,myCat,https://github.com/yumiaura/myCat,197,19,197,1,Python,2026-07-28
```

You can load this into:
- Python + matplotlib/pandas
- Gnuplot
- LibreOffice Calc / Excel
- Any graphing tool

---

## GitHub Token

You need a GitHub Personal Access Token with at least `public_repo` or `repo` scope.

For traffic data, the token must have push access to the target repositories. For popularity data, any token with public repo read access works.

**Security tip:** store your token in `~/.github_token` or `.env` instead of passing it on the command line:

```bash
echo "GITHUB_TOKEN=ghp_xxx" > .env
```

---

## Requirements

- Python 3.10+
- `requests` library

```bash
pip install requests
```

---

## License

Public domain / do whatever you want.
