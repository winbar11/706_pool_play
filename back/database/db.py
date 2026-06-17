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
            phone       TEXT,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Add phone column to existing deployments that predate it
    cur.execute("""
        ALTER TABLE users ADD COLUMN IF NOT EXISTS phone TEXT
    """)
    cur.execute("""
        ALTER TABLE users ADD COLUMN IF NOT EXISTS paid INTEGER DEFAULT 0
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
            final_score INTEGER DEFAULT 0,
            bonus_shots INTEGER DEFAULT 0,
            is_locked   INTEGER DEFAULT 0,
            dk_total_points REAL DEFAULT 0,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    cur.execute("INSERT INTO tournament_settings (key, value) VALUES ('tournament_complete', '0') ON CONFLICT (key) DO NOTHING")
    cur.execute("INSERT INTO tournament_settings (key, value) VALUES ('pot_amount', '0') ON CONFLICT (key) DO NOTHING")
    cur.execute("INSERT INTO tournament_settings (key, value) VALUES ('theme', 'masters') ON CONFLICT (key) DO NOTHING")

    # Allow multiple teams per user (removes the old single-team constraint)
    cur.execute("ALTER TABLE teams DROP CONSTRAINT IF EXISTS teams_user_id_key")

    # Add scoring columns missing from original schema
    cur.execute("ALTER TABLE teams ADD COLUMN IF NOT EXISTS final_score INTEGER DEFAULT 0")
    cur.execute("ALTER TABLE teams ADD COLUMN IF NOT EXISTS bonus_shots INTEGER DEFAULT 0")

    cur.execute("""
        CREATE TABLE IF NOT EXISTS password_reset_tokens (
            token       TEXT PRIMARY KEY,
            user_id     INTEGER NOT NULL REFERENCES users(id),
            expires_at  TIMESTAMP NOT NULL,
            used        INTEGER DEFAULT 0,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    cur.close()
    conn.close()
    _seed_golfers()


GOLFER_SEED_DATA = [
    # 2026 US Open field — DK salaries from DKSalaries.csv
    # (espn_id, name, salary, world_rank, country)
        ("9478",    "Scottie Scheffler",            12300, 1,   "USA"),
        ("3470",    "Rory McIlroy",                 12300, 2,   "NIR"),
        ("9780",    "Jon Rahm",                     11700, 8,   "ESP"),
        ("10046",   "Bryson DeChambeau",            11000, 32,  "USA"),
        ("4425906", "Cameron Young",                10500, 3,   "USA"),
        ("10140",   "Xander Schauffele",            10100, 12,  "USA"),
        ("5539",    "Tommy Fleetwood",              9700,  6,   "ENG"),
        ("4375972", "Ludvig Åberg",                 9500,  13,  "SWE"),
        ("6798",    "Brooks Koepka",                9300,  110, "USA"),
        ("9037",    "Matthew Fitzpatrick",          8900,  4,   "ENG"),
        ("5553",    "Tyrrell Hatton",               8700,  21,  "ENG"),
        ("10592",   "Collin Morikawa",              8500,  10,  "USA"),
        ("569",     "Justin Rose",                  8400,  7,   "ENG"),
        ("4848",    "Justin Thomas",                8300,  16,  "USA"),
        ("4690755", "Chris Gotterup",               8200,  11,  "USA"),
        ("4364873", "Viktor Hovland",               8100,  28,  "NOR"),
        ("5409",    "Russell Henley",               8000,  5,   "USA"),
        ("5579",    "Patrick Reed",                 7900,  27,  "USA"),
        ("11119",   "Wyndham Clark",                7800,  34,  "USA"),
        ("9938",    "Sam Burns",                    7700,  30,  "USA"),
        ("5860",    "Hideki Matsuyama",             7600,  24,  "JPN"),
        ("10166",   "J.J. Spaun",                   7500,  9,   "USA"),
        ("11099",   "Joaquín Niemann",              7400,  80,  "CHI"),
        ("6007",    "Patrick Cantlay",              7300,  36,  "USA"),
        ("7081",    "Si Woo Kim",                   7200,  18,  "KOR"),
        ("4587",    "Shane Lowry",                  7100,  44,  "IRL"),
        ("5467",    "Jordan Spieth",                7100,  51,  "USA"),
        ("4404992", "Ben Griffin",                  7000,  15,  "USA"),
        ("11378",   "Robert MacIntyre",             7000,  17,  "SCO"),
        ("8961",    "Sepp Straka",                  7000,  19,  "AUT"),
        ("4410932", "Min Woo Lee",                  7700,  35,  "AUS"),
        ("4348470", "Kristoffer Reitan",            6900,  26,  "NOR"),
        ("9131",    "Cameron Smith",                6900,  136, "AUS"),
        ("10906",   "Aaron Rai",                    6800,  14,  "ENG"),
        ("9843",    "Jake Knapp",                   6800,  43,  "USA"),
        ("9530",    "Maverick McNealy",             6800,  37,  "USA"),
        ("9484",    "Alex Smalley",                 6800,  42,  "USA"),
        ("11250",   "Nicolai Højgaard",             6700,  33,  "DEN"),
        ("5408",    "Harris English",               6700,  22,  "USA"),
        ("1680",    "Jason Day",                    6700,  47,  "AUS"),
        ("4901368", "Rickie Fowler",                6700,  41,  "USA"),
        ("5338",    "Bud Cauley",                   6600,  40,  "USA"),
        ("4419142", "Akshay Bhatia",                6600,  29,  "USA"),
        ("388",     "Adam Scott",                   6600,  49,  "AUS"),
        ("3550",    "Gary Woodland",                6600,  45,  "USA"),
        ("5076021", "Ryan Gerard",                  6600,  23,  "USA"),
        ("4364865", "Alex Fitzpatrick",             6600,  69,  "ENG"),
        ("9126",    "Corey Conners",                6500,  30,  "CAN"),
        ("10364",   "Kurt Kitayama",                6500,  31,  "USA"),
        ("5054388", "Jacob Bridgeman",              6500,  25,  "USA"),
        ("4895429", "David Puig",                   6500,  57,  "ESP"),
        ("9025",    "Daniel Berger",                6500,  46,  "USA"),
        ("4513",    "Keegan Bradley",               6400,  39,  "USA"),
        ("11382",   "Sungjae Im",                   6400,  74,  "KOR"),
        ("3832",    "Alex Noren",                   6400,  20,  "SWE"),
        ("10980",   "Sahith Theegala",              6400,  83,  "USA"),
        ("5532",    "Carlos Ortiz",                 6400,  125, "MEX"),
        ("4251",    "Ryan Fox",                     6400,  55,  "NZL"),
        ("3792",    "Nick Taylor",                  6300,  63,  "CAN"),
        ("3448",    "Dustin Johnson",               6300,  35,  "USA"),
        ("5215013", "Jackson Koivun",               6300,  145, "USA"),
        ("10343",   "Lucas Herbert",                6300,  146, "AUS"),
        ("10505",   "J.T. Poston",                  6300,  38,  "USA"),
        ("4602673", "Tom Kim",                      6200,  141, "KOR"),
        ("8906",    "Keith Mitchell",               6200,  100, "USA"),
        ("1225",    "Brian Harman",                 6200,  59,  "USA"),
        ("4589438", "Harry Hall",                   6200,  66,  "ENG"),
        ("4602218", "Davis Thompson",               6200,  138, "USA"),
        ("4426181", "Samuel Stevens",               6200,  54,  "USA"),
        ("8974",    "Michael Kim",                  6100,  50,  "USA"),
        ("11332",   "Andrew Novak",                 6100,  61,  "USA"),
        ("4858572", "Ryo Hisatsune",                6100,  62,  "JAP"),
        ("11101",   "Max Greyserman",               6100,  68,  "USA"),
        ("5217048", "Johnny Keefer",                6100,  75,  "USA"),
        ("5143175", "Sudarshan Yellamaraju",        6100,  96,  "CAN"),
        ("4837368", "Pierceson Coody",              6100,  58,  "USA"),
        ("4921329", "Michael Brennan",              6000,  60,  "USA"),
        ("4901368", "Matt McCarty",                 6000,  53,  "USA"),
        ("4604053", "Jayden Schaper",               6000,  70,  "RSA"),
        ("4566443", "Matti Schmid",                 6000,  71,  "GER"),
        ("3449",    "Chris Kirk",                   6000,  106, "USA"),
        ("5502",    "Andrew Putnam",                5900,  85,  "USA"),
        ("4390719", "Matthew Jordan",               5900,  322, "USA"),
        ("4408316", "Nicolas Echavarria",           5900,  52,  "COL"),
        ("6825",    "Patrick Rodgers",              5900,  81,  "USA"),
        ("1651",    "Billy Horschel",               5900,  135, "USA"),
        ("5110034", "Caleb Surratt",                5900,  323, "USA"),
        ("11383",   "Max McGreevy",                 5800,  323, "USA"),
        ("5882",    "Emiliano Grillo",              5800,  116, "ARG"),
        ("5550",    "Laurie Canter",                5800,  151, "ENG"),
        ("4671",    "John Parry",                   5800,  102, "ENG"),
        ("1674",    "Peter Uihlein",                5800,  181, "USA"),
        ("10914",   "Nathan Kimsey",                5800,  323, "USA"),
        ("9040",    "Zac Blair",                    5800,  323, "USA"),
        ("6922",    "Ben Kohles",                   5700,  184, "USA"),
        ("5076011", "Adrien Dumont de Chassart",    5700,  168, "BEL"),
        ("4408320", "Kevin Roy",                    5700,  133, "USA"),
        ("4382434",  "Niklas Nørgaard Moller",      5700,  210, "DEN"),
        ("5077389",  "Ben James",                   5700,  220, "USA"),
        ("301",      "Graeme McDowell",             5700,  208, "NIR"),
        ("5209442",  "Neal Shipley",                5700,  190, "USA"),
        ("5076025",  "William Mouw",                5600,  248, "USA"),
        ("4982182",  "Chandler Phillips",           5600,  210, "USA"),
        ("4348444",  "Jackson Suber",               5600,  128, "USA"),
        ("11253",   "Cole Hammer",                  5600,  85,  "USA"),
        ("8910",    "Ben Silverman",                5600,  175, "CAN"),
        ("4418567", "Ugo Coussaud",                 5600,  170, "FRA"),
        ("4423323",  "Dylan Wu",                    5600,  155, "USA"),
        ("10048",   "Nick Hardy",                   5500,  700, "USA"),
        ("186",    "Padraig Harrington",            5500,  70,  "IRL"),
        ("4372851", "Taylor Montgomery",            5500,  999, "USA"),
        ("1097",    "Jimmy Stanger",                5500,  128, "USA"),
        ("5289692", "Rocco Repetto Taylor",         5500,  999, "ESP"),
        ("686",     "Miles Russell ",               5500,  999, "USA"),
        ("9899",    "Hennie Du Plessis",            5500,  195, "RSA"),
        ("9951",     "Carl Yuan",                   5400,  200, "CHN"),
        ("6952",    "Adrien Saddier",               5400,  115, "FRA"),
        ("11469",    "Angel Hidalgo",               5400,  190, "ESP"),
        ("4691550", "Taihei Sato",                  5400,  403, "JPN"),
        ("5293232", "Alejandro Tosti",              5400,  999, "ARG"),
        ("4683800", "James Nicholas",               5400,  220, "USA"),
        ("4844",    "Harry Higgs",                  5400,  999, "USA"),
        ("4567001", "T.K. Kim",                     5300,  999, "KOR"),
        ("4355673", "Brandon Wu",                   5300,  999, "USA"),
        ("5210226", "Preston Stout",                5300,  999, "USA"),
        ("5344766", "Jackson Herrington",           5300,  999, "USA"),
        ("5293232",  "Ethan Fang",                  5300,  999, "USA"),
        ("4884239", "Filippo Celli",                5300,  999, "ITA"),
        ("5289813", "Bryan Lee",                    5300,  999, "USA"),
        ("5027437", "Cooper Dossey",                5200,  999, "USA"),
        ("5203535", "Jackson Van Paris",            5200,  999, "USA"),
        ("5343786", "Hamilton Coleman",             5200,  999, "USA"),
        ("5362517", "Ryder Cowan",                  5200,  999, "USA"),
        ("5362520", "Chase Kyes",                   5200,  999, "USA"),
        ("5362521", "Eric Lee",                     5200,  999, "USA"),
        ("5277550", "Robbie Higgins",               5200,  999, "USA"),
        ("4425905", "Spencer Tibbits",              5200,  999, "USA"),
        ("5362518", "Marek Fleming",                5100,  999, "USA"),
        ("5362519", "Vaughn Harber",                5100,  999, "USA"),
        ("10994",   "Manav Shah",                   5100,  999, "USA"),
        ("2201886", "Brandon Holtz",                5100,  999, "USA"),
        ("5289811", "Mason Howell",                 5100,  999, "USA"),
        ("4894340", "Kaito Onishi",                 5100,  999, "JPN"),
        ("7120",    "Marcelo Rozo",                 5100,  999, "USA"),
        ("5289156", "Jake Sollon",                  5100,  999, "USA"),
        ("5362526", "Jack Schoenberger",            5100,  999, "USA"),
        ("5362522", "Logan Reilly",                 5000,  999, "USA"),
        ("5362523", "Matthew Robles",               5000,  999, "USA"),
        ("1067",    "J.B. Holmes",                  5000,  999, "USA"),
        ("4699297", "Ryuichi Oiwa",                 5000,  999, "JPN"),
        ("5326067", "Jake Peacock",                 5000,  999, "USA"),
        ("5272338", "Giuseppe Puebla",              5000,  999, "USA"),
        ("5344763", "Mateo Pulcini",                5000,  999, "USA"),
        ("5327840", "Greyson nLeach",               5000,  999, "USA"),
        ("5360549", "Jackson Ormond",               5000,  999, "USA"),
        ("5362524", "Arni Sveinsson",               5000,  999, "USA"),
]


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

    for i, (espn_id, name, salary, rank, country) in enumerate(GOLFER_SEED_DATA):
        unique_espn = f"{espn_id}_{i}"
        cur.execute("""
            INSERT INTO golfers (espn_id, name, salary, world_rank, country)
            VALUES (%s, %s, %s, %s, %s)
        """, (unique_espn, name, salary, rank, country))

    conn.commit()
    cur.close()
    conn.close()


def sync_golfer_rankings():
    """Sync all seed fields (name, salary, world_rank, country) for existing golfers without touching teams."""
    conn = get_conn()
    cur = conn.cursor()
    updated = 0
    for i, (espn_id, name, salary, rank, country) in enumerate(GOLFER_SEED_DATA):
        unique_espn = f"{espn_id}_{i}"
        cur.execute(
            "UPDATE golfers SET name=%s, world_rank=%s, salary=%s, country=%s WHERE espn_id=%s",
            (name, rank, salary, country, unique_espn)
        )
        updated += cur.rowcount
    conn.commit()
    cur.close()
    conn.close()
    return updated