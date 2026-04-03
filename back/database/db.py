import os
import psycopg
from psycopg.rows import dict_row

DATABASE_URL = os.environ.get("DATABASE_URL", "")

def get_conn():
    url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    conn = psycopg.connect(url, row_factory=dict_row, sslmode="require")
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          SERIAL PRIMARY KEY,
            username    TEXT UNIQUE NOT NULL,
            email       TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_admin    INTEGER DEFAULT 0,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS golfers (
            id              SERIAL PRIMARY KEY,
            espn_id         TEXT UNIQUE,
            name            TEXT NOT NULL,
            salary          INTEGER NOT NULL DEFAULT 0,
            world_rank      INTEGER,
            country         TEXT,
            current_round   INTEGER DEFAULT 0,
            round1_score    INTEGER,
            round2_score    INTEGER,
            round3_score    INTEGER,
            round4_score    INTEGER,
            total_score     INTEGER,
            made_cut        INTEGER DEFAULT 1,
            finish_position INTEGER,
            solo_leader_r1  INTEGER DEFAULT 0,
            solo_leader_r2  INTEGER DEFAULT 0,
            solo_leader_r3  INTEGER DEFAULT 0,
            solo_leader_r4  INTEGER DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            id          SERIAL PRIMARY KEY,
            user_id     INTEGER NOT NULL REFERENCES users(id),
            team_name   TEXT NOT NULL,
            total_salary INTEGER NOT NULL,
            is_locked   INTEGER DEFAULT 0,
            dk_total_points REAL DEFAULT 0,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS team_golfers (
            team_id     INTEGER NOT NULL REFERENCES teams(id),
            golfer_id   INTEGER NOT NULL REFERENCES golfers(id),
            PRIMARY KEY (team_id, golfer_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tournament_settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    cur.execute("INSERT INTO tournament_settings (key, value) VALUES ('teams_locked', '0') ON CONFLICT (key) DO NOTHING")
    cur.execute("INSERT INTO tournament_settings (key, value) VALUES ('current_round', '0') ON CONFLICT (key) DO NOTHING")
    cur.execute("INSERT INTO tournament_settings (key, value) VALUES ('tournament_year', '2026') ON CONFLICT (key) DO NOTHING")

    conn.commit()
    cur.close()
    conn.close()
    _seed_golfers()


def _seed_golfers():
    """Seed golfers only if the table is empty."""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as n FROM golfers")
    count = cur.fetchone()["n"]
    if count > 0:
        cur.close()
        conn.close()
        return

    golfers = [
        # (espn_id, name, salary, world_rank, country)
        ("5539",  "Tommy Fleetwood",          10500, 1,  "ENG"),
        ("4375972",  "Ludvig Aberg",          10100, 2,  "SWE"),
        ("5409",  "Russell Henley",           9800, 3,  "USA"),
        ("11378",  "Robert MacIntyre",        9900, 4,  "SCO"),
        ("7081",  "Si Woo Kim",               9600, 5,  "KOR"),
        ("5467",  "Jordan Spieth",            9500, 6,  "USA"),
        ("5001",  "Sepp Straka",              9200, 7,  "AUT"),
        ("3911",  "Hideki Matsuyama",         9100, 8,  "JPN"),
        ("5002",  "Maverick McNealy",         9000, 9,  "USA"),
        ("5003",  "Alex Noren",               8700, 10, "SWE"),
        ("5004",  "Rickie Fowler",            8600, 11, "USA"),
        ("5005",  "Michael Thorbjornsen",     8500, 12, "USA"),
        ("5006",  "Denny McCarthy",           8200, 13, "USA"),
        ("5007",  "Nick Taylor",              8100, 14, "CAN"),
        ("5008",  "Keith Mitchell",           8000, 15, "USA"),
        ("5009",  "J.J. Spaun",               7900, 16, "USA"),
        ("5010",  "Brian Harman",             7900, 17, "USA"),
        ("5011",  "Ryo Hisatsune",            7800, 18, "JPN"),
        ("5012",  "Marco Penge",              7800, 19, "ENG"),
        ("5013",  "Thorbjorn Olesen",         7800, 20, "DEN"),
        ("4448",  "Tony Finau",               7400, 21, "USA"),
        ("5014",  "Stephan Jaeger",           7400, 22, "GER"),
        ("5015",  "Davis Thompson",           7500, 23, "USA"),
        ("5016",  "Andrew Novak",             7300, 24, "USA"),
        ("5019",  "Will Zalatoris",           7100, 26, "USA"),
        ("5020",  "Alex Smalley",             7000, 27, "USA"),
        ("5021",  "Lucas Glover",             7200, 28, "USA"),
        ("5023",  "Tom Kim",                  7300, 30, "KOR"),
        ("5024",  "Ricky Castillo",           6900, 31, "USA"),
        ("5025",  "Jordan Smith",             6800, 32, "ENG"),
        ("5026",  "Johnny Keefer",            6700, 33, "USA"),
        ("5027",  "Bud Cauley",               6900, 34, "USA"),
        ("5028",  "Andrew Putnam",            6800, 35, "USA"),
        ("5029",  "Chris Kirk",               6700, 36, "USA"),
        ("5030",  "Charley Hoffman",          6600, 37, "USA"),
        ("5031",  "Billy Horschel",           7000, 38, "USA"),
        ("5032",  "Jhonattan Vegas",          6600, 39, "VEN"),
        ("5033",  "Nick Hardy",               6500, 40, "USA"),
        ("5036",  "Sudarshan Yellamaraju",    6500, 43, "USA"),
        ("5037",  "Jimmy Walker",             6400, 44, "USA"),
        ("8973",  "Max Homa",                 7700, 45, "USA"),
        ("5039",  "Webb Simpson",             6600, 46, "USA"),
        ("5040",  "Nick Dunlap",              7200, 47, "USA"),
        ("5041",  "Austin Eckroat",           6900, 48, "USA"),
        ("5042",  "Ryan Gerard",              6800, 49, "USA"),
        ("5043",  "Tom Hoge",                 6600, 50, "USA"),
        ("5044",  "Patrick Rodgers",          6500, 51, "USA"),
        ("5045",  "Mackenzie Hughes",         6500, 52, "CAN"),
        ("5046",  "Emiliano Grillo",          6700, 53, "ARG"),
        ("5047",  "Erik van Rooyen",          6600, 54, "RSA"),
        ("5048",  "J.T. Poston",              6800, 55, "USA"),
        ("5049",  "Adam Schenk",              6500, 56, "USA"),
        ("5050",  "Kristoffer Reitan",        6600, 57, "NOR"),
        ("5051",  "Adrien Saddier",           6400, 58, "FRA"),
        ("5052",  "John Parry",               6400, 59, "ENG"),
        ("5053",  "Haotong Li",               6500, 60, "CHN"),
        ("5054",  "Dan Brown",                6400, 61, "ENG"),
        ("5055",  "Matthieu Pavon",           6800, 62, "FRA"),
        ("5056",  "Karl Vilips",              6700, 63, "AUS"),
        ("5057",  "Sami Valimaki",            6500, 64, "FIN"),
        ("5058",  "Kevin Yu",                 6600, 65, "TPE"),
        ("5059",  "Rafael Campos",            6500, 66, "PUR"),
        ("5060",  "Garrick Higgo",            6400, 67, "RSA"),
        ("5061",  "Joe Highsmith",            6400, 68, "USA"),
        ("5062",  "Brice Garnett",            6300, 69, "USA"),
        ("5063",  "Matt McCarty",             6300, 70, "USA"),
        ("5064",  "Peter Malnati",            6300, 71, "USA"),
        ("5065",  "William Mouw",             6300, 72, "USA"),
        ("5066",  "Steven Fisk",              6300, 73, "USA"),
        ("5067",  "Patton Kizzire",           6300, 74, "USA"),
        ("5068",  "Rico Hoey",                6400, 75, "PHI"),
        ("5069",  "Max McGreevy",             6300, 76, "USA"),
        ("5070",  "Vince Whaley",             6300, 77, "USA"),
        ("5071",  "Eric Cole",                6400, 78, "USA"),
        ("5072",  "Christiaan Bezuidenhout",  6500, 79, "RSA"),
        ("5073",  "Mac Meissner",             6300, 80, "USA"),
        ("5074",  "Kevin Roy",                6200, 81, "USA"),
        ("5075",  "Mark Hubbard",             6300, 82, "USA"),
        ("5076",  "Chad Ramey",               6300, 83, "USA"),
        ("5077",  "Chandler Phillips",        6200, 84, "USA"),
        ("5078",  "Danny Walker",             6200, 85, "USA"),
        ("5079",  "Takumi Kanaya",            6200, 86, "JPN"),
        ("5080",  "Michael Kim",              6300, 87, "USA"),
        ("5081",  "Chandler Blanchet",        6200, 88, "USA"),
        ("5082",  "Austin Smotherman",        6200, 89, "USA"),
        ("5083",  "Neal Shipley",             6300, 90, "USA"),
        ("5084",  "Hank Lebioda",             6200, 91, "USA"),
        ("5085",  "Adrien Dumont de Chassart",6200, 92, "BEL"),
        ("5086",  "S.H. Kim",                 6200, 93, "KOR"),
        ("5087",  "Christo Lamprecht",        6200, 94, "RSA"),
        ("5088",  "Davis Chatfield",          6100, 95, "USA"),
        ("5089",  "Zach Bauchou",             6100, 96, "USA"),
        ("5090",  "Jeffrey Kang",             6100, 97, "USA"),
        ("5091",  "Kensei Hirata",            6100, 98, "JPN"),
        ("5092",  "John VanDerLaan",          6100, 99, "USA"),
        ("5093",  "Zecheng Dou",              6100, 100, "CHN"),
        ("5094",  "Pontus Nyholm",            6100, 101, "SWE"),
        ("5095",  "A.J. Ewart",               6100, 102, "USA"),
        ("5096",  "Alejandro Tosti",          6200, 103, "ARG"),
        ("5097",  "Adam Svensson",            6200, 104, "CAN"),
        ("5098",  "Marcelo Rozo",             6100, 105, "COL"),
        ("5099",  "Dylan Wu",                 6100, 106, "USA"),
        ("5100",  "Luke Clanton",             6300, 107, "USA"),
        ("5101",  "Gordon Sargent",           6300, 108, "USA"),
        ("5102",  "David Ford",               6200, 109, "USA"),
        ("5103",  "Lee Hodges",               6300, 110, "USA"),
        ("5104",  "Matt Wallace",             6200, 111, "ENG"),
        ("5105",  "Beau Hossler",             6200, 112, "USA"),
        ("5106",  "David Lipsky",             6200, 113, "USA"),
        ("5107",  "Patrick Fishburn",         6100, 114, "USA"),
        ("5108",  "Brendon Todd",             6200, 115, "USA"),
        ("5109",  "K.H. Lee",                 6200, 116, "KOR"),
        ("5110",  "Kevin Streelman",          6100, 117, "USA"),
        ("5111",  "Jimmy Stanger",            6100, 118, "USA"),
        ("5112",  "Paul Waring",              6100, 119, "ENG"),
        ("5113",  "Jesper Svensson",          6100, 120, "SWE"),
        ("5114",  "Doug Ghim",                6200, 121, "USA"),
        ("5115",  "Kris Ventura",             6100, 122, "USA"),
        ("5116",  "Seamus Power",             6300, 123, "IRL"),
        ("5117",  "Ryan Palmer",              6100, 124, "USA"),
        ("5118",  "Bronson Burgoon",          6100, 125, "USA"),
        ("5119",  "Brandt Snedeker",          6100, 126, "USA"),
        ("5120",  "Camilo Villegas",          6100, 127, "COL"),
        ("5121",  "Austin Wylie",             6100, 128, "USA"),
        ("5122",  "Patrick Fishburn",         6100, 129, "USA"),
        ("5123",  "Garrick Higgo",            6400, 130, "RSA"),
        ("5124",  "Isaiah Salinda",           6100, 131, "USA"),
        ("5125",  "Aaron Wise",               6100, 132, "USA"),
    ]

    for i, (espn_id, name, salary, rank, country) in enumerate(golfers):
        unique_espn = f"{espn_id}_{i}"
        cur.execute("""
            INSERT INTO golfers (espn_id, name, salary, world_rank, country)
            VALUES (%s, %s, %s, %s, %s)
        """, (unique_espn, name, salary, rank, country))

    conn.commit()
    cur.close()
    conn.close()