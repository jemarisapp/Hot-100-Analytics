### Music Charts DB quick guide

This folder holds a small SQLite database (`charts.db`) and a loader script (`quick_db_loader.py`). Use these steps to add or update chart data.

### 1) Open the folder in PowerShell
```powershell
cd ".\folder"
python .\quick_db_loader.py --db .\charts.db --week 2025-08-16 --chart "Week of August 16th" --csv .\weekly_charts\add_2025-08-16.csv --mode replace
```

If you see a Python prompt like `>>>`, exit it first:
```python
exit()
```

### 2) CSV format (copy/paste this header)
```
Rank,+/-,Song,Artist,Points,Points%,Peak,WoC,Sales,Sales%,Streams,Streams%,Airplay,Airplay%,Units
```

Rules:
- Numbers can use k/m/b (e.g., `5.5k`, `29.4m`).
- Percentages can include `%` (e.g., `-5%`).
- Rank change accepts `=`, `NEW`, `RE`, `RC`, or `+/-` numbers.
- Multiple artists are auto-split on `,`, `&`, `feat./ft.`, `x`, `and`, `with`.

### 3) Add or update entries for an existing week
1) Put only the rows you want to add/change into a CSV, e.g. `add_2025-08-09.csv`.
2) Run:
```powershell
```

What happens:
- Rows are upserted by `(week, rank)`. New ranks insert; existing ranks update; other ranks remain.

### 4) Create a new week
Prepare a CSV for that week and run (change the date and filename):

```powershell
python .\quick_db_loader.py --db .\charts.db --week 2025-08-09 --chart "Week of August 9th" --csv .\add_2025-08-09.csv --mode replace
```

```powershell
python .\quick_db_loader.py --db .\charts.db --week 2025-08-09 --chart "Week of August 16th" --csv .\add_2025-08-16.csv --mode replace
```

### 5) Verify quickly
Show how many entries the DB has for a week:
```powershell
python -c "import sqlite3; c=sqlite3.connect('charts.db').cursor(); wid=c.execute(\"select id from chart_weeks where chart_name=? and week_date=?\", ('Hybrid Popularity Top 100','2025-08-09')).fetchone()[0]; print('entries:', c.execute('select count(*) from chart_entries where chart_week_id=?',(wid,)).fetchone()[0])"
```

### 6) Notes
- The DB schema stores `artists`, `songs`, a many-to-many `song_artists` table, `chart_weeks`, and `chart_entries` with sales/streams/airplay/units.
- You can safely re-run the same command; it will update the same ranks for that week.

### 7) Common issues
- If a command errors with `>>>` visible, you are inside a Python REPL. Type `exit()` and run again.
- If a CSV is empty or has a different header, nothing will load; ensure the header matches exactly.



