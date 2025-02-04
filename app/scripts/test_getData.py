# File: scripts/test_getData.py

import json
import httpx
import pytest
from datetime import datetime
from uuid import uuid4, UUID

# Import the functions we want to test from getData.py
from app.scripts.getData import (
    fetch_emerging_threats,
    fetch_feodotracker_threats,
    fetch_urlhaus_threats,
    deduplicate_threats,
    convert_to_orm,
    getData,
)

# These are used to construct and inspect Threat objects.
from app.schemas import Threat
from app.models import Threat as SQLAThreat


# ======================
# Helpers for faking HTTP responses
# ======================


class FakeResponse:
    """A fake response object that mimics an httpx.Response."""

    def __init__(self, text=None, json_data=None):
        self.text = text
        self._json_data = json_data

    def json(self):
        return self._json_data


def fake_httpx_get(url):
    """
    A fake version of httpx.get that returns predetermined responses
    based on the URL.
    """
    if url == "https://rules.emergingthreats.net/fwrules/emerging-Block-IPs.txt":
        # Return some lines including a comment, valid IPs and an invalid IP.
        fake_text = (
            "# This is a comment\n" "192.168.1.1/24\n" "10.0.0.1/32\n" "invalid_ip/32\n"
        )
        return FakeResponse(text=fake_text)
    elif url == "https://feodotracker.abuse.ch/downloads/ipblocklist.json":
        fake_json = [{"ip_address": "8.8.8.8"}, {"ip_address": "8.8.4.4"}]
        return FakeResponse(json_data=fake_json)
    elif url == "https://urlhaus.abuse.ch/downloads/json_online/":
        fake_json = {
            "1": [{"url": "http://malicious.com"}],
            "2": [{"url": "http://evil.com"}],
        }
        return FakeResponse(json_data=fake_json)
    else:
        return FakeResponse(text="")


# ======================
# Helpers for faking a database session
# ======================


class FakeQuery:
    """A fake query object that implements distinct() for testing."""

    def __init__(self, values):
        self.values = values

    def distinct(self):
        # Return a list of one-item tuples to simulate SQLAlchemy query results.
        return [(v,) for v in self.values]


class FakeDB:
    """
    A fake DB session that implements only the parts needed for getData().
    It records any objects added so that you can verify them.
    """

    def __init__(self, ips=None, urls=None):
        # ips and urls represent values already in the DB.
        self._ips = ips or []
        self._urls = urls or []
        self.added = []  # to record objects added via add_all
        self.committed = False
        self.closed = False

    def query(self, col):
        # Here we use the string representation of the column to decide
        # which set to return. (SQLAlchemy columns typically include the column name.)
        col_str = str(col)
        if "ipv4" in col_str:
            return FakeQuery(self._ips)
        elif "url" in col_str:
            return FakeQuery(self._urls)
        return FakeQuery([])

    def add_all(self, items):
        self.added.extend(items)

    def commit(self):
        self.committed = True

    def close(self):
        self.closed = True


# ======================
# Pytest Fixtures
# ======================


@pytest.fixture(autouse=True)
def patch_httpx_get(monkeypatch):
    """
    Automatically override httpx.get in every test so that the fake version is used.
    """
    monkeypatch.setattr(httpx, "get", fake_httpx_get)


@pytest.fixture
def fake_get_db(monkeypatch):
    """
    Replace the get_db function (imported in getData.py) with one that yields a FakeDB.
    This fake DB is initialized with no existing IPs or URLs, so that deduplication
    does not remove any new threats.
    """
    fake_db = FakeDB(ips=[], urls=[])
    # Import the getData module (not just the getData() function) to override get_db.
    import app.scripts.getData as getData_module

    monkeypatch.setattr(getData_module, "get_db", lambda: iter([fake_db]))
    return fake_db


# ======================
# Tests for each function
# ======================


def test_fetch_emerging_threats():
    threats = fetch_emerging_threats()
    # In our fake response, the valid IPs are "192.168.1.1" and "10.0.0.1"
    ips = [t.ipv4 for t in threats]
    assert "192.168.1.1" in ips
    assert "10.0.0.1" in ips
    # The invalid IP should have been skipped.
    assert len(threats) == 2

    # Check additional attributes.
    for t in threats:
        assert isinstance(t.id, UUID)
        assert (
            t.source
            == "https://rules.emergingthreats.net/fwrules/emerging-Block-IPs.txt"
        )


def test_fetch_feodotracker_threats():
    threats = fetch_feodotracker_threats()
    ips = [t.ipv4 for t in threats]
    assert "8.8.8.8" in ips
    assert "8.8.4.4" in ips
    assert len(threats) == 2

    for t in threats:
        assert isinstance(t.id, UUID)
        assert t.source == "https://feodotracker.abuse.ch/downloads/ipblocklist.json"
        # Check that original_data contains "ip_address".
        # t.original_data may be a JSON string or already a dict depending on your model's behavior.
        if isinstance(t.original_data, str):
            data = json.loads(t.original_data)
        else:
            data = t.original_data
        assert "ip_address" in data


def test_fetch_urlhaus_threats():
    threats = fetch_urlhaus_threats()
    urls = [t.url for t in threats]
    assert "http://malicious.com" in urls
    assert "http://evil.com" in urls
    assert len(threats) == 2

    for t in threats:
        assert isinstance(t.id, UUID)
        assert t.source == "https://urlhaus.abuse.ch/downloads/json_online/"
        # Check that original_data contains "url".
        if isinstance(t.original_data, str):
            data = json.loads(t.original_data)
        else:
            data = t.original_data
        assert "url" in data


def test_deduplicate_threats():
    # Create two Threat objects.
    threat1 = Threat(
        id=uuid4(),
        ipv4="192.168.1.1",
        date=datetime.now(),
        source="test_source",
        original_data=None,
        url=None,
    )
    threat2 = Threat(
        id=uuid4(),
        ipv4="10.0.0.1",
        date=datetime.now(),
        source="test_source",
        original_data=None,
        url="http://example.com",
    )

    # Create a FakeDB that already contains threat1's IP and threat2's URL.
    fake_db = FakeDB(ips=["192.168.1.1"], urls=["http://example.com"])

    # Both threats should be considered duplicates.
    new_threats = deduplicate_threats([threat1, threat2], fake_db)
    assert new_threats == []

    # Now add a new threat.
    threat3 = Threat(
        id=uuid4(),
        ipv4="8.8.8.8",
        date=datetime.now(),
        source="test_source",
        original_data=None,
        url="http://newsite.com",
    )
    fake_db = FakeDB(ips=["192.168.1.1"], urls=["http://example.com"])
    new_threats = deduplicate_threats([threat1, threat2, threat3], fake_db)
    # Only threat3 is new.
    assert len(new_threats) == 1
    assert new_threats[0].ipv4 == "8.8.8.8"
    assert new_threats[0].url == "http://newsite.com"


def test_convert_to_orm():
    # Create one Threat object.
    threat = Threat(
        id=uuid4(),
        ipv4="1.2.3.4",
        date=datetime.now(),
        source="test_source",
        original_data=json.dumps({"key": "value"}),
        url="http://example.com",
    )
    orm_threats = convert_to_orm([threat])
    # Expect one ORM object.
    assert len(orm_threats) == 1
    orm = orm_threats[0]
    # Verify that the fields were copied correctly.
    assert orm.ipv4 == threat.ipv4
    assert orm.url == threat.url
    assert orm.source == threat.source

    # Compare the actual data by loading the JSON string.
    # threat.original_data might be a dict already or a JSON string.
    if isinstance(threat.original_data, str):
        expected_data = json.loads(threat.original_data)
    else:
        expected_data = threat.original_data

    # orm.original_data is a JSON string, so load it before comparing.
    actual_data = json.loads(orm.original_data)
    assert actual_data == expected_data


def test_getData(fake_get_db):
    """
    Test the complete getData() function. With our fake HTTP responses,
    getData() will fetch:
      - 2 emerging threats,
      - 2 feodotracker threats, and
      - 2 URLhaus threats,
    for a total of 6 threats. Since our FakeDB starts empty,
    none are duplicates.
    """
    getData()
    # Our fake_get_db fixture provides the fake DB that getData() uses.
    # Verify that 6 ORM threat objects were added.
    assert len(fake_get_db.added) == 6
    # Verify that commit() and close() were called.
    assert fake_get_db.committed is True
    assert fake_get_db.closed is True
