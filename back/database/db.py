import os
from contextlib import contextmanager

from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.orm import sessionmaker

from database.models import Base, Golfer

DATABASE_URL = os.environ.get("DATABASE_URL", "")


def _sqlalchemy_url(url: str) -> str:
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


PGSSLMODE = os.environ.get("PGSSLMODE", "prefer")

engine = create_engine(_sqlalchemy_url(DATABASE_URL), connect_args={"sslmode": PGSSLMODE})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def to_dict(obj) -> dict:
    return {c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs}


def init_db():
    Base.metadata.create_all(engine)

    with engine.begin() as conn:
        # Backward-compat statements for deployments that predate these columns/constraints
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS phone TEXT"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS paid INTEGER DEFAULT 0"))
        conn.execute(text("ALTER TABLE teams DROP CONSTRAINT IF EXISTS teams_user_id_key"))
        conn.execute(text("ALTER TABLE teams ADD COLUMN IF NOT EXISTS final_score INTEGER DEFAULT 0"))
        conn.execute(text("ALTER TABLE teams ADD COLUMN IF NOT EXISTS bonus_shots INTEGER DEFAULT 0"))

        conn.execute(text(
            "INSERT INTO tournament_settings (key, value) VALUES ('teams_locked', '0') ON CONFLICT (key) DO NOTHING"
        ))
        conn.execute(text(
            "INSERT INTO tournament_settings (key, value) VALUES ('current_round', '0') ON CONFLICT (key) DO NOTHING"
        ))
        conn.execute(text(
            "INSERT INTO tournament_settings (key, value) VALUES ('tournament_year', '2026') ON CONFLICT (key) DO NOTHING"
        ))
        conn.execute(text(
            "INSERT INTO tournament_settings (key, value) VALUES ('tournament_complete', '0') ON CONFLICT (key) DO NOTHING"
        ))
        conn.execute(text(
            "INSERT INTO tournament_settings (key, value) VALUES ('pot_amount', '0') ON CONFLICT (key) DO NOTHING"
        ))
        conn.execute(text(
            "INSERT INTO tournament_settings (key, value) VALUES ('theme', 'masters') ON CONFLICT (key) DO NOTHING"
        ))

    _seed_golfers()


GOLFER_SEED_DATA = [
    # 2026 Open Championship field — DK salaries from open_champ_salaries_26.csv, espn_id/country from ESPN leaderboard (event 401811957), world_rank is a salary-order proxy (no OWGR data available)
    # (espn_id, name, salary, world_rank, country)
        ("9478"     , "Scottie Scheffler",           12000, 1, "USA"),
        ("3470"     , "Rory McIlroy",                11900, 2, "NIR"),
        ("5539"     , "Tommy Fleetwood",             10500, 3, "ENG"),
        ("9037"     , "Matt Fitzpatrick",            10000, 4, "ENG"),
        ("10140"    , "Xander Schauffele",           9800, 5, "USA"),
        ("9780"     , "Jon Rahm",                    9700, 6, "ESP"),
        ("4375972"  , "Ludvig Åberg",                9300, 7, "SWE"),
        ("569"      , "Justin Rose",                 9100, 8, "ENG"),
        ("4425906"  , "Cameron Young",               9000, 9, "USA"),
        ("5553"     , "Tyrrell Hatton",              8900, 10, "ENG"),
        ("10592"    , "Collin Morikawa",             8700, 11, "USA"),
        ("4690755"  , "Chris Gotterup",              8500, 12, "USA"),
        ("10046"    , "Bryson DeChambeau",           8400, 13, "USA"),
        ("4364873"  , "Viktor Hovland",              8300, 14, "NOR"),
        ("11119"    , "Wyndham Clark",               8200, 15, "USA"),
        ("11378"    , "Robert MacIntyre",            8000, 16, "SCO"),
        ("4587"     , "Shane Lowry",                 7900, 17, "IRL"),
        ("9938"     , "Sam Burns",                   7800, 18, "USA"),
        ("5409"     , "Russell Henley",              7700, 19, "USA"),
        ("6798"     , "Brooks Koepka",               7600, 20, "USA"),
        ("4848"     , "Justin Thomas",               7500, 21, "USA"),
        ("4364865"  , "Alex Fitzpatrick",            7400, 22, "ENG"),
        ("11099"    , "Joaquín Niemann",             7300, 23, "CHI"),
        ("5467"     , "Jordan Spieth",               7200, 24, "USA"),
        ("10906"    , "Aaron Rai",                   7100, 25, "ENG"),
        ("6007"     , "Patrick Cantlay",             7000, 26, "USA"),
        ("5579"     , "Patrick Reed",                7000, 27, "USA"),
        ("5860"     , "Hideki Matsuyama",            6900, 28, "JPN"),
        ("7081"     , "Si Woo Kim",                  6900, 29, "KOR"),
        ("4410932"  , "Min Woo Lee",                 6900, 30, "AUS"),
        ("4602673"  , "Tom Kim",                     6800, 31, "KOR"),
        ("4404992"  , "Ben Griffin",                 6800, 32, "USA"),
        ("9131"     , "Cameron Smith",               6800, 33, "AUS"),
        ("9126"     , "Corey Conners",               6800, 34, "CAN"),
        ("9530"     , "Maverick McNealy",            6700, 35, "USA"),
        ("4585549"  , "Marco Penge",                 6700, 36, "ENG"),
        ("10166"    , "J.J. Spaun",                  6700, 37, "USA"),
        ("5408"     , "Harris English",              6700, 38, "USA"),
        ("9843"     , "Jake Knapp",                  6700, 39, "USA"),
        ("4565467"  , "Eugenio Lopez-Chacarra",      6700, 40, "ESP"),
        ("1225"     , "Brian Harman",                6600, 41, "USA"),
        ("11250"    , "Nicolai Højgaard",            6600, 42, "DEN"),
        ("4419142"  , "Akshay Bhatia",               6600, 43, "USA"),
        ("8961"     , "Sepp Straka",                 6600, 44, "AUT"),
        ("10364"    , "Kurt Kitayama",               6500, 45, "USA"),
        ("4348470"  , "Kristoffer Reitan",           6500, 46, "NOR"),
        ("3702"     , "Rickie Fowler",               6500, 47, "USA"),
        ("388"      , "Adam Scott",                  6500, 48, "AUS"),
        ("4895429"  , "David Puig",                  6500, 49, "ESP"),
        ("4513"     , "Keegan Bradley",              6500, 50, "USA"),
        ("5054388"  , "Jacob Bridgeman",             6400, 51, "USA"),
        ("8973"     , "Max Homa",                    6400, 52, "USA"),
        ("3832"     , "Alex Noren",                  6400, 53, "SWE"),
        ("1680"     , "Jason Day",                   6400, 54, "AUS"),
        ("5076021"  , "Ryan Gerard",                 6400, 55, "USA"),
        ("4251"     , "Ryan Fox",                    6300, 56, "NZL"),
        ("4589438"  , "Harry Hall",                  6300, 57, "ENG"),
        ("11253"    , "Rasmus Højgaard",             6300, 58, "DEN"),
        ("3550"     , "Gary Woodland",               6300, 59, "USA"),
        ("10548"    , "Matt Wallace",                6300, 60, "ENG"),
        ("11382"    , "Sungjae Im",                  6200, 61, "KOR"),
        ("4604053"  , "Jayden Trey Schaper",         6200, 62, "RSA"),
        ("4858859"  , "Rasmus Neergaard-Petersen",   6200, 63, "DEN"),
        ("5105333"  , "Angel Ayora Fanegas",         6200, 64, "ESP"),
        ("9025"     , "Daniel Berger",               6200, 65, "USA"),
        ("9221"     , "Hao-Tong Li",                 6200, 66, "CHN"),
        ("10980"    , "Sahith Theegala",             6200, 67, "USA"),
        ("10505"    , "J.T. Poston",                 6100, 68, "USA"),
        ("4837"     , "Thomas Detry",                6100, 69, "BEL"),
        ("9506"     , "Jordan L. Smith",             6100, 70, "ENG"),
        ("8906"     , "Keith Mitchell",              6100, 71, "USA"),
        ("4858572"  , "Ryo Hisatsune",               6100, 72, "JPN"),
        ("10343"    , "Lucas Herbert",               6100, 73, "AUS"),
        ("5338"     , "Bud Cauley",                  6000, 74, "USA"),
        ("11101"    , "Max Greyserman",              6000, 75, "USA"),
        ("4348444"  , "Tom McKibbin",                6000, 76, "NIR"),
        ("4610056"  , "Casey Jarvis",                6000, 77, "RSA"),
        ("10522"    , "Eric Cole",                   6000, 78, "USA"),
        ("9484"     , "Alex Smalley",                6000, 79, "USA"),
        ("11332"    , "Andrew Novak",                5900, 80, "USA"),
        ("3792"     , "Nick Taylor",                 5900, 81, "CAN"),
        ("1293"     , "Louis Oosthuizen",            5900, 82, "RSA"),
        ("4921329"  , "Michael Brennan",             5900, 83, "USA"),
        ("4837368"  , "Pierceson Coody",             5900, 84, "USA"),
        ("4425899"  , "Daniel Hillier",              5900, 85, "NZL"),
        ("4317"     , "Bernd Wiesberger",            5800, 86, "AUT"),
        ("1651"     , "Billy Horschel",              5800, 87, "USA"),
        ("8974"     , "Michael Kim",                 5800, 88, "USA"),
        ("4671"     , "John Parry",                  5800, 89, "ENG"),
        ("4592246"  , "Frederic Lacroix",            5800, 90, "FRA"),
        ("9963"     , "Scott Vincent",               5800, 91, "ZIM"),
        ("4390719"  , "Matthew Jordan",              5700, 92, "ENG"),
        ("4426181"  , "Sam Stevens",                 5700, 93, "USA"),
        ("4699329"  , "Jesper Svensson",             5700, 94, "SWE"),
        ("4585548"  , "Sami Välimäki",               5700, 95, "FIN"),
        ("4982182"  , "Jackson Suber",               5700, 96, "USA"),
        ("9899"     , "Hennie Du Plessis",           5700, 97, "RSA"),
        ("4901368"  , "Matthew McCarty",             5600, 98, "USA"),
        ("5716"     , "Francesco Laporta",           5600, 99, "ITA"),
        ("1407"     , "Daniel Brown",                5600, 100, "ENG"),
        ("5152205"  , "Josele Ballester",            5600, 101, "ESP"),
        ("5550"     , "Laurie Canter",               5600, 102, "ENG"),
        ("1674"     , "Peter Uihlein",               5600, 103, "USA"),
        ("1483"     , "Francesco Molinari",          5600, 104, "ITA"),
        ("4408316"  , "Nicolas Echavarria",          5500, 105, "COL"),
        ("4425907"  , "Alistair Docherty",           5500, 106, "USA"),
        ("4407372"  , "Antoine Rozner",              5500, 107, "FRA"),
        ("5956"     , "Andy Sullivan",               5500, 108, "ENG"),
        ("186"      , "Padraig Harrington",          5500, 109, "IRL"),
        ("78"       , "Stewart Cink",                5500, 110, "USA"),
        ("5057"     , "Shaun Norris",                5500, 111, "RSA"),
        ("4699418"  , "Keita Nakajima",              5400, 112, "JPN"),
        ("5102625"  , "Martin Couvra",               5400, 113, "FRA"),
        ("5186648"  , "Kazuma Kobori",               5400, 114, "NZL"),
        ("5081630"  , "Dan Bradbury",                5400, 115, "ENG"),
        ("5110034"  , "Caleb Surratt",               5400, 116, "USA"),
        ("5312609"  , "Kota Kaneko",                 5400, 117, "JPN"),
        ("7110"     , "MJ Daffue",                   5400, 118, "RSA"),
        ("6962"     , "Adrien Saddier",              5300, 119, "FRA"),
        ("5727"     , "Joakim Lagergren",            5300, 120, "SWE"),
        ("7067"     , "Michael Hollick",             5300, 121, "RSA"),
        ("5852"     , "Matthew Southgate",           5300, 122, "ENG"),
        ("4837226"  , "Naoyuki Kataoka",             5300, 123, "JPN"),
        ("5337673"  , "Jack Buchanan",               5300, 124, "RSA"),
        ("4592199"  , "Jeongwoo Ham",                5300, 125, "KOR"),
        ("4872728"  , "Sam Bairstow",                5200, 126, "ENG"),
        ("11345"    , "Travis Smyth",                5200, 127, "AUS"),
        ("576"      , "Henrik Stenson",              5200, 128, "SWE"),
        ("4699328"  , "Ren Yonezawa",                5200, 129, "JPN"),
        ("4683800"  , "James Nicholas",              5200, 130, "USA"),
        ("5832"     , "Matthew Baldwin",             5200, 131, "ENG"),
        ("5147926"  , "Tim Wiedemeyer",              5200, 132, "GER"),
        ("4597553"  , "Kazuki Higa",                 5200, 133, "JPN"),
        ("4368981"  , "Cameron John",                5200, 134, "AUS"),
        ("9379"     , "Austen Truslow",              5100, 135, "USA"),
        ("4699375"  , "Ryutaro Nagano",              5100, 136, "JPN"),
        ("5062278"  , "Lev Grinberg",                5100, 137, "FRA"),
        ("5075661"  , "Marcus Plunkett",             5100, 138, "USA"),
        ("5364787"  , "Stuart Grehan",               5100, 139, "IRL"),
        ("6849"     , "Jack McDonald",               5100, 140, "SCO"),
        ("82"       , "Darren Clarke",               5100, 141, "NIR"),
        ("5146173"  , "Tiger Christensen",           5100, 142, "GER"),
        ("5289811"  , "Mason Howell",                5100, 143, "USA"),
        ("5289694"  , "Baard Bjoernevik Skogen",     5000, 144, "NOR"),
        ("11270"    , "Thomas Sloman",               5000, 145, "ENG"),
        ("5327297"  , "Fifa Laopakdee",              5000, 146, "THA"),
        ("5289808"  , "Nevill Ruiter",               5000, 147, "NED"),
        ("5143177"  , "Jiho Yang",                   5000, 148, "KOR"),
        ("5369475"  , "Alejandro De Castro Piera",   5000, 149, "ESP"),
        ("5344763"  , "Mateo Pulcini",               5000, 150, "ARG"),
        ("5369476"  , "David Howard",                5000, 151, "IRL"),
        ("115"      , "David Duval",                 5000, 152, "USA"),
]


def _seed_golfers():
    """Seed golfers only if the table is empty."""
    with get_session() as session:
        count = session.query(Golfer).count()
        if count > 0:
            return

        for i, (espn_id, name, salary, rank, country) in enumerate(GOLFER_SEED_DATA):
            unique_espn = f"{espn_id}_{i}"
            session.add(Golfer(
                espn_id=unique_espn, name=name, salary=salary,
                world_rank=rank, country=country,
            ))


def sync_golfer_rankings():
    """Sync all seed fields (espn_id, name, salary, world_rank, country) for existing golfers without touching teams."""
    updated = 0
    with get_session() as session:
        for i, (espn_id, name, salary, rank, country) in enumerate(GOLFER_SEED_DATA):
            unique_espn = f"{espn_id}_{i}"
            golfer = session.execute(
                select(Golfer).where(Golfer.espn_id == unique_espn)
            ).scalar_one_or_none()

            if golfer is None:
                # espn_id changed in seed data — find by name and update espn_id too
                golfer = session.execute(
                    select(Golfer).where(Golfer.name == name)
                ).scalar_one_or_none()

            if golfer is None:
                continue

            golfer.espn_id = unique_espn
            golfer.name = name
            golfer.world_rank = rank
            golfer.salary = salary
            golfer.country = country
            updated += 1

    return updated
