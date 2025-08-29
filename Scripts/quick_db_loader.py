import argparse
import csv
import io
import re
import sqlite3
from typing import List


SAMPLE_CSV = """Rank,+/-,Song,Artist,Points,Points%,Peak,WoC,Sales,Sales%,Streams,Streams%,Airplay,Airplay%,Units
1,=,Ordinary,Alex Warren,224,-5%,1,25,5.5k,2%,19.5m,58%,70.7m,40%,131.2k
2,=,Golden,"Huntz, Ejae, Audrey Nuna, REI Ami & KPop Dem",220,15%,2,6,5.0k,2%,29.4m,95%,4.9m,3%,212.0k
3,+1,What I Want,"Morgan Wallen feat. Tate McRae",167,-3%,1,11,2.0k,1%,19.8m,82%,22.7m,17%,134.2k
4,-1,Daisies,Justin Bieber,154,-12%,2,3,2.5k,2%,17.5m,85%,16.7m,14%,131.0k
5,=,Just In Case,Morgan Wallen,146,-5%,2,19,1.5k,1%,15.7m,73%,30.5m,26%,103.8k
"""


ARTIST_SEPARATORS = [
    r"\s*,\s*",
    r"\s*&\s*",
    r"\s+feat\.?\s+",
    r"\s+ft\.?\s+",
    r"\s+x\s+",
    r"\s+and\s+",
    r"\s+with\s+",
]

PROTECTED_ARTISTS_WITH_INTERNAL_SEPARATORS = [
    "Tyler, The Creator",
]

def _protect_known_names(text: str) -> str:
    if not text:
        return text
    placeholder = "∯"
    for name in PROTECTED_ARTISTS_WITH_INTERNAL_SEPARATORS:
        safe = name.replace(",", placeholder)
        text = re.sub(re.escape(name), safe, text)
    return text

def _unprotect(text: str) -> str:
    if not text:
        return text
    return text.replace("∯", ",")


def split_artists(artist_field: str) -> List[str]:
    if not artist_field:
        return []
    s = artist_field.strip()
    s = re.sub(r"\((.*?)\)", "", s).strip()
    s = _protect_known_names(s)
    pattern = "(" + "|".join(ARTIST_SEPARATORS) + ")"
    parts = [p.strip() for p in re.split(pattern, s) if p and not re.match(pattern, p)]
    cleaned: List[str] = []
    for p in parts:
        p = re.sub(r"\s+", " ", p).strip().strip(",&/")
        p = _unprotect(p)
        if p:
            cleaned.append(p)
    seen = set()
    uniq: List[str] = []
    for a in cleaned:
        k = a.lower()
        if k not in seen:
            seen.add(k)
            uniq.append(a)
    return uniq


def to_int(x):
    if x is None:
        return None
    s = str(x).strip()
    if s == "" or s.lower() == "na":
        return None
    s = s.replace(",", "")
    m = re.match(r"^([0-9]*\.?[0-9]+)\s*([kKmMbB]?)$", s)
    if m:
        val = float(m.group(1))
        suf = m.group(2).lower()
        mult = 1
        if suf == "k":
            mult = 1_000
        elif suf == "m":
            mult = 1_000_000
        elif suf == "b":
            mult = 1_000_000_000
        return int(round(val * mult))
    try:
        return int(s)
    except ValueError:
        try:
            return int(round(float(s)))
        except ValueError:
            return None


def to_float(x):
    if x is None:
        return None
    s = str(x).strip().replace(",", "")
    if s == "" or s.lower() == "na":
        return None
    if s.endswith("%"):
        s = s[:-1]
    try:
        return float(s)
    except ValueError:
        return None


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS artists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

-- Songs are unique by title + canonical set of primary artists
CREATE TABLE IF NOT EXISTS songs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    canonical_artists TEXT,
    UNIQUE(title, canonical_artists)
);

CREATE TABLE IF NOT EXISTS song_artists (
    song_id INTEGER NOT NULL,
    artist_id INTEGER NOT NULL,
    role TEXT DEFAULT 'primary',
    PRIMARY KEY (song_id, artist_id, role),
    FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE,
    FOREIGN KEY (artist_id) REFERENCES artists(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS chart_weeks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chart_name TEXT NOT NULL,
    week_date TEXT NOT NULL,
    UNIQUE(chart_name, week_date)
);

CREATE TABLE IF NOT EXISTS chart_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chart_week_id INTEGER NOT NULL,
    rank INTEGER NOT NULL,
    rank_change INTEGER,
    points INTEGER,
    points_change_pct REAL,
    peak INTEGER,
    woc INTEGER,
    sales INTEGER,
    sales_share_pct REAL,
    streams INTEGER,
    streams_share_pct REAL,
    airplay INTEGER,
    airplay_share_pct REAL,
    units INTEGER,
    song_id INTEGER NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (chart_week_id) REFERENCES chart_weeks(id) ON DELETE CASCADE,
    FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE,
    UNIQUE(chart_week_id, rank)
);
"""


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_SQL)
    _ensure_songs_schema(conn)
    conn.commit()


def _ensure_songs_schema(conn: sqlite3.Connection) -> None:
    """If an older 'songs' table exists without canonical_artists, migrate it in-place.

    Keeps existing song ids and all foreign key references.
    """
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(songs)")
    cols = [r[1] for r in cur.fetchall()]
    if "canonical_artists" in cols:
        return
    # Migrate: add canonical_artists and unique(title, canonical_artists)
    cur.execute("PRAGMA foreign_keys=OFF")
    cur.executescript(
        """
        CREATE TABLE IF NOT EXISTS songs_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            canonical_artists TEXT,
            UNIQUE(title, canonical_artists)
        );
        INSERT INTO songs_new (id, title, canonical_artists)
        SELECT id, title, NULL FROM songs;
        DROP TABLE songs;
        ALTER TABLE songs_new RENAME TO songs;
        """
    )
    cur.execute("PRAGMA foreign_keys=ON")
    conn.commit()


def upsert_artist(conn: sqlite3.Connection, name: str) -> int:
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO artists(name) VALUES (?)", (name,))
    cur.execute("SELECT id FROM artists WHERE name = ?", (name,))
    return cur.fetchone()[0]


def _canonical_artists_key(artists: List[str]) -> str:
    # Lowercase and sort to normalize equivalent sets
    norm = [re.sub(r"\s+", " ", a).strip().lower() for a in artists]
    norm.sort()
    return "|".join(norm)


def find_or_create_song(conn: sqlite3.Connection, title: str, artists: List[str]) -> int:
    """Find a song by title + primary-artist set; otherwise create it.

    Also ensures song_artists links exist for the provided artists.
    """
    canonical = _canonical_artists_key(artists)
    cur = conn.cursor()
    # Try exact match by title + canonical key first
    cur.execute(
        "SELECT id FROM songs WHERE title = ? AND canonical_artists = ?",
        (title, canonical),
    )
    row = cur.fetchone()
    if row:
        song_id = row[0]
    else:
        # Create new song
        cur.execute(
            "INSERT INTO songs(title, canonical_artists) VALUES (?, ?)",
            (title, canonical),
        )
        song_id = cur.lastrowid
        conn.commit()
    # Ensure song_artists links
    link_song_artists(conn, song_id, artists)
    return song_id


def link_song_artists(conn: sqlite3.Connection, song_id: int, artists: List[str]) -> None:
    cur = conn.cursor()
    for a in artists:
        aid = upsert_artist(conn, a)
        cur.execute(
            "INSERT OR IGNORE INTO song_artists(song_id, artist_id, role) VALUES (?, ?, 'primary')",
            (song_id, aid),
        )
    conn.commit()


def upsert_chart_week(conn: sqlite3.Connection, chart_name: str, week_date: str) -> int:
    cur = conn.cursor()
    cur.execute(
        "INSERT OR IGNORE INTO chart_weeks(chart_name, week_date) VALUES (?, ?)",
        (chart_name, week_date),
    )
    cur.execute(
        "SELECT id FROM chart_weeks WHERE chart_name = ? AND week_date = ?",
        (chart_name, week_date),
    )
    return cur.fetchone()[0]


def parse_rank_change(raw: str) -> int:
    if raw is None or str(raw).strip() == "":
        return 0
    s = str(raw).strip()
    if s in {"=", "0"}:
        return 0
    if s.upper() in {"RE", "NEW", "RC"}:
        return 0
    try:
        return int(s)
    except ValueError:
        m = re.match(r"^([+-]?\d+)", s)
        if m:
            return int(m.group(1))
        return 0


def load_rows(conn: sqlite3.Connection, rows: List[dict], chart_name: str, week_date: str, mode: str = "upsert") -> None:
    week_id = upsert_chart_week(conn, chart_name, week_date)
    print(f"Using week_id: {week_id} for {chart_name} on {week_date}")  # Debug print
    cur = conn.cursor()
    if mode == "replace":
        # Remove any existing entries for this chart week before inserting
        cur.execute("DELETE FROM chart_entries WHERE chart_week_id = ?", (week_id,))
        print(f"Deleted existing entries for week_id: {week_id}")  # Add this debug print
    
    for row in rows:
        title = (row.get("Song") or "").strip()
        artists_field = (row.get("Artist") or "").strip()
        if not title:
            continue
        artists = split_artists(artists_field) or []
        song_id = find_or_create_song(conn, title, artists)

        payload = (
            week_id,  # This should be 6 for August 16th
            to_int(row.get("Rank")),
            parse_rank_change(row.get("+/-")),
            to_int(row.get("Points")),
            to_float(row.get("Points%")),
            to_int(row.get("Peak")),
            to_int(row.get("WoC")),
            to_int(row.get("Sales")),
            to_float(row.get("Sales%")),
            to_int(row.get("Streams")),
            to_float(row.get("Streams%")),
            to_int(row.get("Airplay")),
            to_float(row.get("Airplay%")),
            to_int(row.get("Units")),
            song_id,
        )
        print(f"Inserting rank {to_int(row.get('Rank'))} with week_id: {week_id}")  # Add this debug print
        cur.execute(
            """
            INSERT INTO chart_entries (
                chart_week_id, rank, rank_change, points, points_change_pct, peak, woc,
                sales, sales_share_pct, streams, streams_share_pct, airplay, airplay_share_pct,
                units, song_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(chart_week_id, rank) DO UPDATE SET
                rank_change=excluded.rank_change,
                points=excluded.points,
                points_change_pct=excluded.points_change_pct,
                peak=COALESCE(excluded.peak, chart_entries.peak),
                woc=excluded.woc,
                sales=excluded.sales,
                sales_share_pct=excluded.sales_share_pct,
                streams=excluded.streams,
                streams_share_pct=excluded.streams_share_pct,
                airplay=excluded.airplay,
                airplay_share_pct=excluded.airplay_share_pct,
                units=excluded.units
            ;
            """,
            payload,
        )
        print(f"Successfully inserted rank {to_int(row.get('Rank'))}")  # Add this debug print
    conn.commit()
    print(f"Finished loading {len(rows)} rows for week_id: {week_id}")  # Add this debug print


def load_from_csv_text(csv_text: str) -> List[dict]:
    f = io.StringIO(csv_text.strip())
    reader = csv.DictReader(f)
    return list(reader)


def load_from_csv_file(path: str) -> List[dict]:
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def main():
    parser = argparse.ArgumentParser(description="Create and populate charts.db from CSV or sample")
    parser.add_argument("--db", default="charts.db", help="SQLite DB file path")
    parser.add_argument("--week", default="2025-08-09", help="Week date (YYYY-MM-DD)")
    parser.add_argument("--chart", default="Hybrid Popularity Top 100", help="Chart name")
    parser.add_argument("--csv", help="Optional CSV file to load instead of the built-in sample")
    parser.add_argument("--use-sample", action="store_true", help="Load the built-in 5-row sample")
    parser.add_argument("--mode", choices=["upsert", "replace"], default="upsert",
                        help="upsert updates/inserts by (week, rank); replace deletes the entire week before insert")
    args = parser.parse_args()

    if not args.use_sample and not args.csv:
        print("Specify --csv PATH or use --use-sample", flush=True)
        return

    rows = load_from_csv_text(SAMPLE_CSV) if args.use_sample else load_from_csv_file(args.csv)

    conn = sqlite3.connect(args.db)
    try:
        init_db(conn)
        load_rows(conn, rows, chart_name=args.chart, week_date=args.week, mode=args.mode)
        print(f"Loaded {len(rows)} row(s) into {args.db} for week {args.week} using mode={args.mode}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()


