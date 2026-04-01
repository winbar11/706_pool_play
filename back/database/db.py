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
        INSERT OR IGNORE INTO tournament_settings VALUES ('tournament_year', '2026');
    """)

    conn.commit()
    conn.close()
    _seed_golfers()


def _seed_golfers():
    """Seed the 2026 Valero Texas Open full field with DK salaries."""
    golfers = [
        # (espn_id, name, salary, world_rank, country)
        ("5001", "Tommy Fleetwood",         10500, 1,  "ENG"),
        ("5002", "Ludvig Aberg",            10100, 2,  "SWE"),
        ("5003", "Russell Henley",           9800, 3,  "USA"),
        ("5004", "Robert MacIntyre",         9900, 4,  "SCO"),
        ("5005", "Si Woo Kim",               9600, 5,  "KOR"),
        ("5006", "Jordan Spieth",            9500, 6,  "USA"),
        ("5007", "Sepp Straka",              9200, 7,  "AUT"),
        ("5008", "Hideki Matsuyama",         9100, 8,  "JPN"),
        ("5009", "Maverick McNealy",         9000, 9,  "USA"),
        ("5010", "Alex Noren",               8700, 10, "SWE"),
        ("5011", "Rickie Fowler",            8600, 11, "USA"),
        ("5012", "Michael Thorbjornsen",     8500, 12, "USA"),
        ("5013", "Denny McCarthy",           8200, 13, "USA"),
        ("5014", "Nick Taylor",              8100, 14, "CAN"),
        ("5015", "Keith Mitchell",           8000, 15, "USA"),
        ("5016", "J.J. Spaun",               7900, 16, "USA"),
        ("5017", "Brian Harman",             7900, 17, "USA"),
        ("5018", "Ryo Hisatsune",            7800, 18, "JPN"),
        ("5019", "Marco Penge",              7800, 19, "ENG"),
        ("5020", "Thorbjorn Olesen",         7800, 20, "DEN"),
        ("5021", "Tony Finau",               7400, 21, "USA"),
        ("5022", "Stephan Jaeger",           7400, 22, "GER"),
        ("5023", "Davis Thompson",           7500, 23, "USA"),
        ("5024", "Andrew Novak",             7300, 24, "USA"),
        ("5025", "Daniel Berger",            7600, 25, "USA"),
        ("5026", "Will Zalatoris",           7100, 26, "USA"),
        ("5027", "Alex Smalley",             7000, 27, "USA"),
        ("5028", "Lucas Glover",             7200, 28, "USA"),
        ("5029", "Sahith Theegala",          7400, 29, "USA"),
        ("5030", "Tom Kim",                  7300, 30, "KOR"),
        ("5031", "Ricky Castillo",           6900, 31, "USA"),
        ("5032", "Jordan Smith",             6800, 32, "ENG"),
        ("5033", "Bud Cauley",               6900, 33, "USA"),
        ("5034", "Andrew Putnam",            6800, 34, "USA"),
        ("5035", "Chris Kirk",               6700, 35, "USA"),
        ("5036", "Charley Hoffman",          6600, 36, "USA"),
        ("5037", "Billy Horschel",           7000, 37, "USA"),
        ("5038", "Jhonattan Vegas",          6600, 38, "VEN"),
        ("5039", "Jake Knapp",               6800, 39, "USA"),
        ("5040", "Chris Gotterup",           6700, 40, "USA"),
        ("5041", "Sudarshan Yellamaraju",    6500, 41, "USA"),
        ("5042", "Jimmy Walker",             6400, 42, "USA"),
        ("5043", "Max Homa",                 7700, 43, "USA"),
        ("5044", "Webb Simpson",             6600, 44, "USA"),
        ("5045", "Nick Dunlap",              7200, 45, "USA"),
        ("5046", "Austin Eckroat",           6900, 46, "USA"),
        ("5047", "Ryan Gerard",              6800, 47, "USA"),
        ("5048", "Tom Hoge",                 6600, 48, "USA"),
        ("5049", "Patrick Rodgers",          6500, 49, "USA"),
        ("5050", "Mackenzie Hughes",         6500, 50, "CAN"),
        ("5051", "Emiliano Grillo",          6700, 51, "ARG"),
        ("5052", "Erik van Rooyen",          6600, 52, "RSA"),
        ("5053", "J.T. Poston",              6800, 53, "USA"),
        ("5054", "Adam Schenk",              6500, 54, "USA"),
        ("5055", "Kristoffer Reitan",        6600, 55, "NOR"),
        ("5056", "Adrien Saddier",           6400, 56, "FRA"),
        ("5057", "John Parry",               6400, 57, "ENG"),
        ("5058", "Haotong Li",               6500, 58, "CHN"),
        ("5059", "Dan Brown",                6400, 59, "ENG"),
        ("5060", "Matthieu Pavon",           6800, 60, "FRA"),
        ("5061", "Karl Vilips",              6700, 61, "AUS"),
        ("5062", "Sami Valimaki",            6500, 62, "FIN"),
        ("5063", "Kevin Yu",                 6600, 63, "TPE"),
        ("5064", "Rafael Campos",            6500, 64, "PUR"),
        ("5065", "Garrick Higgo",            6400, 65, "RSA"),
        ("5066", "Joe Highsmith",            6400, 66, "USA"),
        ("5067", "Brice Garnett",            6300, 67, "USA"),
        ("5068", "Matt McCarty",             6300, 68, "USA"),
        ("5069", "Peter Malnati",            6300, 69, "USA"),
        ("5070", "William Mouw",             6300, 70, "USA"),
        ("5071", "Steven Fisk",              6300, 71, "USA"),
        ("5072", "Patton Kizzire",           6300, 72, "USA"),
        ("5073", "Rico Hoey",                6400, 73, "PHI"),
        ("5074", "Max McGreevy",             6300, 74, "USA"),
        ("5075", "Vince Whaley",             6300, 75, "USA"),
        ("5076", "Eric Cole",                6400, 76, "USA"),
        ("5077", "Christiaan Bezuidenhout",  6500, 77, "RSA"),
        ("5078", "Mac Meissner",             6300, 78, "USA"),
        ("5079", "Kevin Roy",                6200, 79, "USA"),
        ("5080", "Mark Hubbard",             6300, 80, "USA"),
        ("5081", "Chad Ramey",               6300, 81, "USA"),
        ("5082", "Chandler Phillips",        6200, 82, "USA"),
        ("5083", "Danny Walker",             6200, 83, "USA"),
        ("5084", "Takumi Kanaya",            6200, 84, "JPN"),
        ("5085", "Michael Kim",              6300, 85, "USA"),
        ("5086", "Johnny Keefer",            6700, 86, "USA"),
        ("5087", "Chandler Blanchet",        6200, 87, "USA"),
        ("5088", "Austin Smotherman",        6200, 88, "USA"),
        ("5089", "Neal Shipley",             6300, 89, "USA"),
        ("5090", "Hank Lebioda",             6200, 90, "USA"),
        ("5091", "Adrien Dumont de Chassart",6200, 91, "BEL"),
        ("5092", "S.H. Kim",                 6200, 92, "KOR"),
        ("5093", "Christo Lamprecht",        6200, 93, "RSA"),
        ("5094", "Davis Chatfield",          6100, 94, "USA"),
        ("5095", "Zach Bauchou",             6100, 95, "USA"),
        ("5096", "Jeffrey Kang",             6100, 96, "USA"),
        ("5097", "Kensei Hirata",            6100, 97, "JPN"),
        ("5098", "John VanDerLaan",          6100, 98, "USA"),
        ("5099", "Zecheng Dou",              6100, 99, "CHN"),
        ("5100", "Pontus Nyholm",            6100, 100, "SWE"),
        ("5101", "A.J. Ewart",              6100, 101, "USA"),
        ("5102", "Alejandro Tosti",          6200, 102, "ARG"),
        ("5103", "Adam Svensson",            6200, 103, "CAN"),
        ("5104", "Marcelo Rozo",             6100, 104, "COL"),
        ("5105", "Dylan Wu",                 6100, 105, "USA"),
        ("5106", "Luke Clanton",             6300, 106, "USA"),
        ("5107", "Gordon Sargent",           6300, 107, "USA"),
        ("5108", "David Ford",               6200, 108, "USA"),
        ("5109", "Lee Hodges",               6300, 109, "USA"),
        ("5110", "Matt Wallace",             6200, 110, "ENG"),
        ("5111", "Beau Hossler",             6200, 111, "USA"),
        ("5112", "David Lipsky",             6200, 112, "USA"),
        ("5113", "Patrick Fishburn",         6100, 113, "USA"),
        ("5114", "Brendon Todd",             6200, 114, "USA"),
        ("5115", "K.H. Lee",                 6200, 115, "KOR"),
        ("5116", "Kevin Streelman",          6100, 116, "USA"),
        ("5117", "Jimmy Stanger",            6100, 117, "USA"),
        ("5118", "Paul Waring",              6100, 118, "ENG"),
        ("5119", "Jesper Svensson",          6100, 119, "SWE"),
        ("5120", "Doug Ghim",                6200, 120, "USA"),
        ("5121", "Kris Ventura",             6100, 121, "USA"),
        ("5122", "Seamus Power",             6300, 122, "IRL"),
        ("5123", "Ryan Palmer",              6100, 123, "USA"),
        ("5124", "Bronson Burgoon",          6100, 124, "USA"),
        ("5125", "Brandt Snedeker",          6100, 125, "USA"),
        ("5126", "Camilo Villegas",          6100, 126, "COL"),
        ("5127", "Austin Wylie",             6100, 127, "USA"),
        ("5128", "Gordon Sargent",           6300, 128, "USA"),
    ]

    conn = get_conn()
    cur = conn.cursor()
    seen_names = set()
    for i, (espn_id, name, salary, rank, country) in enumerate(golfers):
        if name in seen_names:
            continue
        seen_names.add(name)
        unique_espn = f"{espn_id}_{i}"
        cur.execute("""
            INSERT OR IGNORE INTO golfers (espn_id, name, salary, world_rank, country)
            VALUES (?, ?, ?, ?, ?)
        """, (unique_espn, name, salary, rank, country))
    conn.commit()
    conn.close()