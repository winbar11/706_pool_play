import sqlite3
import os

DB_PATH = os.environ.get("DB_PATH", "masters_pool.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT UNIQUE NOT NULL,
            email       TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin    INTEGER DEFAULT 0,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS golfers (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            espn_id     TEXT UNIQUE,
            name        TEXT NOT NULL,
            salary      INTEGER NOT NULL DEFAULT 0,
            world_rank  INTEGER,
            country     TEXT,
            -- Current tournament stats (refreshed end-of-round)
            current_round   INTEGER DEFAULT 0,
            round1_score    INTEGER,
            round2_score    INTEGER,
            round3_score    INTEGER,
            round4_score    INTEGER,
            total_score     INTEGER,
            made_cut        INTEGER DEFAULT 1,  -- 1=in, 0=missed/WD
            finish_position INTEGER,
            -- DK fantasy points (computed end-of-round)
            dk_r1_points    REAL DEFAULT 0,
            dk_r2_points    REAL DEFAULT 0,
            dk_r3_points    REAL DEFAULT 0,
            dk_r4_points    REAL DEFAULT 0,
            dk_total_points REAL DEFAULT 0,
            -- Hole-level bonus tracking
            r1_birdies INTEGER DEFAULT 0, r1_eagles INTEGER DEFAULT 0,
            r1_bogeys  INTEGER DEFAULT 0, r1_doubles INTEGER DEFAULT 0,
            r1_worse   INTEGER DEFAULT 0, r1_pars    INTEGER DEFAULT 0,
            r1_ace     INTEGER DEFAULT 0, r1_double_eagle INTEGER DEFAULT 0,
            r1_bogey_free INTEGER DEFAULT 0, r1_birdie_streak INTEGER DEFAULT 0,
            r2_birdies INTEGER DEFAULT 0, r2_eagles INTEGER DEFAULT 0,
            r2_bogeys  INTEGER DEFAULT 0, r2_doubles INTEGER DEFAULT 0,
            r2_worse   INTEGER DEFAULT 0, r2_pars    INTEGER DEFAULT 0,
            r2_ace     INTEGER DEFAULT 0, r2_double_eagle INTEGER DEFAULT 0,
            r2_bogey_free INTEGER DEFAULT 0, r2_birdie_streak INTEGER DEFAULT 0,
            r3_birdies INTEGER DEFAULT 0, r3_eagles INTEGER DEFAULT 0,
            r3_bogeys  INTEGER DEFAULT 0, r3_doubles INTEGER DEFAULT 0,
            r3_worse   INTEGER DEFAULT 0, r3_pars    INTEGER DEFAULT 0,
            r3_ace     INTEGER DEFAULT 0, r3_double_eagle INTEGER DEFAULT 0,
            r3_bogey_free INTEGER DEFAULT 0, r3_birdie_streak INTEGER DEFAULT 0,
            r4_birdies INTEGER DEFAULT 0, r4_eagles INTEGER DEFAULT 0,
            r4_bogeys  INTEGER DEFAULT 0, r4_doubles INTEGER DEFAULT 0,
            r4_worse   INTEGER DEFAULT 0, r4_pars    INTEGER DEFAULT 0,
            r4_ace     INTEGER DEFAULT 0, r4_double_eagle INTEGER DEFAULT 0,
            r4_bogey_free INTEGER DEFAULT 0, r4_birdie_streak INTEGER DEFAULT 0,
            all4_under70  INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS teams (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL REFERENCES users(id),
            team_name   TEXT NOT NULL,
            total_salary INTEGER NOT NULL,
            is_locked   INTEGER DEFAULT 0,
            dk_total_points REAL DEFAULT 0,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id)
        );

        CREATE TABLE IF NOT EXISTS team_golfers (
            team_id     INTEGER NOT NULL REFERENCES teams(id),
            golfer_id   INTEGER NOT NULL REFERENCES golfers(id),
            PRIMARY KEY (team_id, golfer_id)
        );

        CREATE TABLE IF NOT EXISTS tournament_settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        );

        INSERT OR IGNORE INTO tournament_settings VALUES ('teams_locked', '0');
        INSERT OR IGNORE INTO tournament_settings VALUES ('current_round', '0');
        INSERT OR IGNORE INTO tournament_settings VALUES ('tournament_year', '2025');
    """)

    conn.commit()
    conn.close()
    _seed_golfers()


def _seed_golfers():
    """Seed the 2025 Masters field with realistic DK salaries."""
    golfers = [
        # (espn_id, name, salary, world_rank, country)
        ("4848", "Scottie Scheffler",   11800, 1,  "USA"),
        ("3470", "Rory McIlroy",        10900, 2,  "NIR"),
        ("3448", "Jon Rahm",            9800,  3,  "ESP"),
        ("5467", "Xander Schauffele",   9500,  4,  "USA"),
        ("4362", "Collin Morikawa",     9200,  5,  "USA"),
        ("3836", "Viktor Hovland",      8900,  6,  "NOR"),
        ("3526", "Brooks Koepka",       8700,  7,  "USA"),
        ("9496", "Ludvig Åberg",        8600,  8,  "SWE"),
        ("4474", "Tommy Fleetwood",     8400,  9,  "ENG"),
        ("3213", "Dustin Johnson",      8200, 10,  "USA"),
        ("5765", "Bryson DeChambeau",   8200, 11,  "USA"),
        ("3911", "Patrick Cantlay",     8100, 12,  "USA"),
        ("4924", "Wyndham Clark",       7900, 13,  "USA"),
        ("5765", "Shane Lowry",         7800, 14,  "IRL"),
        ("2329", "Justin Rose",         7600, 15,  "ENG"),
        ("4564", "Hideki Matsuyama",    8300, 16,  "JPN"),
        ("3470", "Tyrrell Hatton",      7700, 17,  "ENG"),
        ("5765", "Robert MacIntyre",    7500, 18,  "SCO"),
        ("4691", "Max Homa",            7700, 19,  "USA"),
        ("3802", "Jordan Spieth",       8000, 20,  "USA"),
        ("3702", "Justin Thomas",       7900, 21,  "USA"),
        ("4448", "Tony Finau",          7500, 22,  "USA"),
        ("5765", "Akshay Bhatia",       7300, 23,  "USA"),
        ("5765", "Sahith Theegala",     7400, 24,  "USA"),
        ("3812", "Jason Day",           7300, 25,  "AUS"),
        ("4311", "Adam Scott",          7100, 26,  "AUS"),
        ("3698", "Sergio Garcia",       6900, 27,  "ESP"),
        ("3777", "Phil Mickelson",      6700, 28,  "USA"),
        ("5765", "Cameron Smith",       7200, 29,  "AUS"),
        ("5765", "Sepp Straka",         7100, 30,  "AUT"),
        ("5765", "Min Woo Lee",         7000, 31,  "AUS"),
        ("5765", "Patrick Reed",        6900, 32,  "USA"),
        ("3449", "Fred Couples",        6500, 33,  "USA"),
        ("5765", "Corey Conners",       6800, 34,  "CAN"),
        ("5765", "Si Woo Kim",          6800, 35,  "KOR"),
        ("5765", "Matt Fitzpatrick",    7600, 36,  "ENG"),
        ("5765", "Keegan Bradley",      6700, 37,  "USA"),
        ("5765", "Nicolai Højgaard",    6600, 38,  "DEN"),
        ("5765", "Harris English",      6500, 39,  "USA"),
        ("5765", "Chris Kirk",          6500, 40,  "USA"),
        ("5765", "Jason Kokrak",        6400, 41,  "USA"),
        ("3231", "Vijay Singh",         6200, 42,  "FIJ"),
        ("5765", "Kevin Kisner",        6300, 43,  "USA"),
        ("5765", "Charley Hoffman",     6300, 44,  "USA"),
        ("5765", "Luke List",           6200, 45,  "USA"),
    ]

    conn = get_conn()
    cur = conn.cursor()
    for i, (espn_id, name, salary, rank, country) in enumerate(golfers):
        unique_espn = f"{espn_id}_{i}"
        cur.execute("""
            INSERT OR IGNORE INTO golfers (espn_id, name, salary, world_rank, country)
            VALUES (?, ?, ?, ?, ?)
        """, (unique_espn, name, salary, rank, country))
    conn.commit()
    conn.close()