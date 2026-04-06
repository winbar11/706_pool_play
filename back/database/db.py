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
    cur.execute("INSERT INTO tournament_settings (key, value) VALUES ('tournament_complete', '0') ON CONFLICT (key) DO NOTHING")
    cur.execute("INSERT INTO tournament_settings (key, value) VALUES ('pot_amount', '0') ON CONFLICT (key) DO NOTHING")

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
        # 2026 Masters Tournament field — DK salaries from DKSalaries.csv
        # (espn_id, name, salary, world_rank, country)
        ("9478",    "Scottie Scheffler",            12000, 1,   "USA"),
        ("3470",    "Rory McIlroy",                 11600, 2,   "NIR"),
        ("10046",   "Bryson DeChambeau",            10200, 8,   "USA"),
        ("9780",    "Jon Rahm",                     10000, 7,    "ESP"),
        ("4375972", "Ludvig Åberg",                 9900,  3,   "SWE"),
        ("10140",   "Xander Schauffele",            9700,  4,   "USA"),
        ("5539",    "Tommy Fleetwood",              9300,  6,   "ENG"),
        ("4425906", "Cameron Young",                9300,  18,  "USA"),
        ("10592",   "Collin Morikawa",              9200,  5,   "USA"),
        ("569",     "Justin Rose",                  9000,  45,  "ENG"),
        ("5579",    "Patrick Reed",                 8900,  55,  "USA"),
        ("5860",    "Hideki Matsuyama",             8900,  12,  "JPN"),
        ("4364873", "Viktor Hovland",               8800,  5,   "NOR"),
        ("9037",    "Matt Fitzpatrick",             8700,  20,  "ENG"),
        ("11378",   "Robert MacIntyre",             8600,  10,  "SCO"),
        ("10166",   "J.J. Spaun",                   8500,  24,  "USA"),
        ("5467",    "Jordan Spieth",                8300,  19,  "USA"),
        ("4848",    "Justin Thomas",                8300,  11,  "USA"),
        ("4587",    "Shane Lowry",                  8200,  15,  "IRL"),
        ("5553",    "Tyrrell Hatton",               8100,  13,  "ENG"),
        ("6798",    "Brooks Koepka",                8100,  14,  "USA"),
        ("4690755", "Chris Gotterup",               8000,  150, "USA"),
        ("8961",    "Sepp Straka",                  8000,  21,  "AUT"),
        ("4419142", "Akshay Bhatia",                8000,  17,  "USA"),
        ("6007",    "Patrick Cantlay",              7900,  11,  "USA"),
        ("5409",    "Russell Henley",               7900,  9,   "USA"),
        ("7081",    "Si Woo Kim",                   7800,  27,  "KOR"),
        ("4410932", "Min Woo Lee",                  7700,  26,  "AUS"),
        ("9126",    "Corey Conners",                7700,  30,  "CAN"),
        ("9843",    "Jake Knapp",                   7700,  42,  "USA"),
        ("4404992", "Ben Griffin",                  7600,  95,  "USA"),
        ("1680",    "Jason Day",                    7600,  50,  "AUS"),
        ("388",     "Adam Scott",                   7500,  40,  "AUS"),
        ("3550",    "Gary Woodland",                7500,  52,  "USA"),
        ("9131",    "Cameron Smith",                7500,  35,  "AUS"),
        ("11382",   "Sungjae Im",                   7500,  25,  "KOR"),
        ("1225",    "Brian Harman",                 7500,  22,  "USA"),
        ("5054388", "Jacob Bridgeman",              7400,  185, "USA"),
        ("9025",    "Daniel Berger",                7400,  38, "USA"),
        ("9938",    "Sam Burns",                    7400,  22,  "USA"),
        ("5408",    "Harris English",               7300,  30,  "USA"),
        ("8973",    "Max Homa",                     7300,  20,  "USA"),
        ("11250",   "Nicolai Højgaard",             7300,  36,  "DEN"),
        ("4585549", "Marco Penge",                  7300,  165, "ENG"),
        ("4901368", "Matt McCarty",                 7300,  49,  "USA"),
        ("9530",    "Maverick McNealy",             7200,  75,  "USA"),
        ("11119",   "Wyndham Clark",                7100,  16,  "USA"),
        ("4251",    "Ryan Fox",                     7100,  65,  "NZL"),
        ("158",     "Sergio Garcia",                7100,  210, "ESP"),
        ("3832",    "Alex Noren",                   7000,  29,  "SWE"),
        ("3448",    "Dustin Johnson",               7000,  35,  "USA"),
        ("4513",    "Keegan Bradley",               7000,  23,  "USA"),
        ("4348444", "Tom McKibbin",                 6900,  135, "NIR"),
        ("11253",   "Rasmus Højgaard",              6900,  85,  "DEN"),
        ("4589438", "Harry Hall",                   6900,  145, "ENG"),
        ("10364",   "Kurt Kitayama",                6800,  65,  "USA"),
        ("5076021", "Ryan Gerard",                  6800,  190, "USA"),
        ("10906",   "Aaron Rai",                    6800,  75,  "ENG"),
        ("4858859", "Rasmus Neergaard-Petersen",    6700,  175, "DEN"),
        ("5217048", "John Keefer",                  6700,  200, "USA"),
        ("4408316", "Nicolas Echavarria",           6700,  90,  "COL"),
        ("8974",    "Michael Kim",                  6700,  205, "USA"),
        ("4921329", "Michael Brennan",              6600,  180, "USA"),
        ("4610056", "Casey Jarvis",                 6600,  170, "RSA"),
        ("5532",    "Carlos Ortiz",                 6600,  125, "MEX"),
        ("11101",   "Max Greyserman",               6600,  105, "USA"),
        ("4585548", "Sami Valimaki",                6500,  155, "FIN"),
        ("3792",    "Nick Taylor",                  6500,  28,  "CAN"),
        ("11332",   "Andrew Novak",                 6400,  130, "USA"),
        ("4426181", "Sam Stevens",                  6400,  70,  "USA"),
        ("10058",   "Davis Riley",                  6400,  70,  "USA"),
        ("4348470", "Kristoffer Reitan",            6300,  140, "NOR"),
        ("9221",    "Haotong Li",                   6300,  999, "CHN"),
        ("1097",    "Charl Schwartzel",             6300,  120, "RSA"),
        ("780",     "Bubba Watson",                 6300,  999, "USA"),
        ("686",     "Zach Johnson",                 6300,  999, "USA"),
        ("5080439", "Aldrich Potgieter",            6200,  195, "RSA"),
        ("4837226", "Naoyuki Kataoka",              6200,  200, "JPN"),
        ("9525",    "Brian Campbell",               6200,  999, "USA"),
        ("4304",    "Danny Willett",                6200,  100, "ENG"),
        ("5344766", "Jackson Herrington (A)",       6100,  999, "USA"),
        ("5293232", "Ethan Fang (A)",               6100,  999, "USA"),
        ("2201886", "Brandon Holtz (A)",            6100,  220, "USA"),
        ("5289811", "Mason Howell (A)",             6100,  999, "USA"),
        ("5327297", "Fifa Laopakdee (A)",           6100,  999, "THA"),
        ("392",     "Vijay Singh",                  6100,  999, "FIJ"),
        ("65",      "Ángel Cabrera",                5900,  999, "ARG"),
        ("91",      "Fred Couples",                 5800,  999, "USA"),
        ("453",     "Mike Weir",                    5800,  999, "CAN"),
        ("5344763", "Mateo Pulcini (A)",            5800,  999, "ARG"),
        ("329",     "José María Olazábal",          5800,  999, "ESP"),
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