from sqlalchemy import select

from database.db import get_session
from database.models import Golfer
from scheduler.scheduler import _unique_match


def make_golfer(name, espn_id=None):
    with get_session() as session:
        g = Golfer(name=name, espn_id=espn_id, salary=5000)
        session.add(g)
        session.flush()
        return g.id


def test_unique_match_returns_sole_match():
    gid = make_golfer("Scottie Scheffler")

    with get_session() as session:
        result = _unique_match(
            session, select(Golfer).where(Golfer.name.like("%Scheffler%")),
            "name", "Scottie Scheffler",
        )
        assert result.id == gid


def test_unique_match_returns_none_on_ambiguous_names():
    # Two golfers whose names share a substring — picking either silently
    # would mis-attribute a score, so this must return None instead of a guess.
    make_golfer("Kevin Smith")
    make_golfer("John Smith")

    with get_session() as session:
        result = _unique_match(
            session, select(Golfer).where(Golfer.name.like("%Smith%")),
            "name", "Smith",
        )
        assert result is None


def test_unique_match_returns_none_on_no_match():
    with get_session() as session:
        result = _unique_match(
            session, select(Golfer).where(Golfer.name.like("%Nobody%")),
            "name", "Nobody",
        )
        assert result is None
