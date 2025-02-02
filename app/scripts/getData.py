import sys

sys.path.insert(0, "../..")

import ipaddress
import json
import httpx
from uuid import uuid4
from datetime import datetime

from app.schemas import Threat
from app.database import get_db
from app.models import Threat as SQLAThreat


def fetch_emerging_threats():
    """
    Fetches and parses the Emerging Threats IP blocklist.
    Returns a list of Threat objects.
    """
    source = "https://rules.emergingthreats.net/fwrules/emerging-Block-IPs.txt"
    response = httpx.get(source)
    lines = response.text.splitlines()

    # Filter out comment lines and blank lines.
    valid_lines = [line for line in lines if line and "#" not in line]

    # Remove CIDR notation (anything after '/').
    ips = [line.split("/")[0] for line in valid_lines]

    parsed_ips = []
    failed_ips = []
    for ip in ips:
        try:
            ipaddress.ip_address(ip)
            parsed_ips.append(ip)
        except ValueError:
            failed_ips.append(ip)

    print("Emerging Threats FW Rules IP Blocklist:")
    print(
        f"{len(lines)} lines downloaded. {len(parsed_ips)} IP addresses parsed. {len(failed_ips)} failed to parse"
    )

    return [
        Threat(
            id=uuid4(),
            ipv4=ip,
            date=datetime.now(),
            source=source,
            original_data=None,
            url=None,
        )
        for ip in parsed_ips
    ]


def fetch_feodotracker_threats():
    """
    Fetches and parses the Feodotracker IP blocklist.
    Returns a list of Threat objects.
    """
    source = "https://feodotracker.abuse.ch/downloads/ipblocklist.json"
    response = httpx.get(source)
    data = response.json()

    print("Feodotracker IP Blocklist:")
    print(f"{len(data)} ips found")

    threats = []
    for entry in data:
        threats.append(
            Threat(
                id=uuid4(),
                ipv4=entry["ip_address"],
                url=None,
                date=datetime.now(),
                source=source,
                original_data=json.dumps(entry),
            )
        )
    return threats


def fetch_urlhaus_threats():
    """
    Fetches and parses the Urlhaus URL blocklist.
    Returns a list of Threat objects.
    """
    source = "https://urlhaus.abuse.ch/downloads/json_online/"
    response = httpx.get(source)
    data = response.json()

    print("Urlhaus url blocklist")
    print(f"{len(data)} urls found")

    threats = []
    for _, value in data.items():
        info = value[0]
        threats.append(
            Threat(
                id=uuid4(),
                ipv4=None,
                url=info["url"],
                date=datetime.now(),
                source=source,
                original_data=json.dumps(info),
            )
        )
    return threats


def deduplicate_threats(threats, db):
    """
    Deduplicates threats based on unique IP and URL entries already in the database.
    Returns a list of new Threat objects.
    """
    seen_urls = {url[0] for url in db.query(SQLAThreat.url).distinct()}
    seen_ips = {
        ip[0] for ip in db.query(SQLAThreat.ipv4).distinct() if ip[0] is not None
    }

    print("Removing duplicate data")
    deduplicated = []
    for threat in threats:
        if threat.url not in seen_urls and threat.ipv4 not in seen_ips:
            if threat.ipv4:
                seen_ips.add(threat.ipv4)
            if threat.url:
                seen_urls.add(threat.url)
            deduplicated.append(threat)

    print(f"{len(deduplicated)} new threats to be added to the database")
    return deduplicated


def convert_to_orm(threats):
    """
    Converts a list of Threat objects into SQLAlchemy ORM Threat objects.
    """
    return [
        SQLAThreat(
            id=str(threat.id),
            ipv4=threat.ipv4,
            url=threat.url,
            date=threat.date,
            source=threat.source,
            original_data=(
                json.dumps(threat.original_data) if threat.original_data else None
            ),
            abuseIPDBData=(
                json.dumps(threat.abuseIPDBData) if threat.abuseIPDBData else None
            ),
        )
        for threat in threats
    ]


def getData():
    # Gather threats from all sources.
    threats = []
    threats.extend(fetch_emerging_threats())
    threats.extend(fetch_feodotracker_threats())
    threats.extend(fetch_urlhaus_threats())

    # Open a database connection.
    db = next(get_db())

    # Deduplicate the threats against those already in the database.
    new_threats = deduplicate_threats(threats, db)

    # Convert Threats to ORM objects.
    db_threats = convert_to_orm(new_threats)

    # Add new threats to the database.
    db.add_all(db_threats)
    db.commit()
    print("Threats added")
    db.close()


def main():
    getData()


if __name__ == "__main__":
    main()
