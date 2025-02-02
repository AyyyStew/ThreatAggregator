# %%
# to fix path issues when running as a notebook is vscode
import sys

sys.path.insert(0, "../..")

# %%
import httpx
import ipaddress
import json
from app.schemas import Threat
from uuid import uuid4
from datetime import datetime
from app.database import get_db
from app.models import Threat as SQLAThreat


def getData():
    # %%
    # container to hold threat data
    threats = []

    # %%
    source = "https://rules.emergingthreats.net/fwrules/emerging-Block-IPs.txt"
    res = httpx.get(source)

    # %%

    # This file is a text file with addresses on each new line
    lines = res.text.split("\n")

    # Parse out the comments and blank lines
    lines = filter(lambda x: False if "#" in x or x == "" else True, lines)
    lines = list(lines)
    # Get rid of CIDR notation
    lines = [x.split("/")[0] for x in lines]

    # %%
    badly_parsed = []
    parsed = []

    # Validate IP address
    for ip in lines:
        try:
            ipaddress.ip_address(ip)
            parsed.append(ip)
        except ValueError as e:
            badly_parsed.append(ip)

    print("Emerging Threats FW Rules IP Blocklist:")
    print(
        f"{len(lines)} lines downloaded. {len(parsed)} IP addressed parsed. {len(badly_parsed)} failed to parse"
    )

    # %%
    for ip in parsed:
        threats.append(
            Threat(
                id=uuid4(),
                ipv4=ip,
                date=datetime.now(),
                source=source,
                original_data=None,
                url=None,
            )
        )

    # %%
    source = "https://feodotracker.abuse.ch/downloads/ipblocklist.json"
    res = httpx.get(source)
    r = res.json()

    # %%
    print("Feodotracker IP Blocklist:")
    print(f"{len(r)} ips found")

    # %%
    for result in r:
        threats.append(
            Threat(
                id=uuid4(),
                ipv4=result["ip_address"],
                url=None,
                date=datetime.now(),
                source=source,
                original_data=json.dumps(result),
            )
        )

    # %%
    source = "https://urlhaus.abuse.ch/downloads/json_online/"
    res = httpx.get(source)
    r = res.json()

    # %%
    print("Urlhaus url blocklist")
    print(f"{len(r)} urls found")

    # %%

    for k, v in r.items():
        info = v[0]
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

    # %%
    # Get all unique urls and ips in the treat database so we don't duplicate data.
    db = next(get_db())

    seen_urls = {url[0] for url in db.query(SQLAThreat.url).distinct()}
    seen_ips = {
        ip[0] for ip in db.query(SQLAThreat.ipv4).distinct() if ip[0] is not None
    }

    # %%
    print("Removing duplicate data")

    # %%
    # Deduplication algorithm. Could have done at each data ingestion phase for speed, but this is easier to read and maintain.
    deduplicated_threats = []
    for threat in threats:
        if threat.url not in seen_urls:
            if threat.ipv4 not in seen_ips:
                if threat.ipv4:
                    seen_ips.add(threat.ipv4)
                if threat.url:
                    seen_urls.add(threat.url)

                deduplicated_threats.append(threat)

    # %%
    print(f"{len(deduplicated_threats)} new threats to be added to the database")

    # %%

    # Convert Threats into ORM objects
    db_threats = [
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
        for threat in deduplicated_threats
    ]

    # Add them to the database
    db.add_all(db_threats)

    db.commit()

    # %%
    print("Threats added")

    # %%
    db.close()


def main():
    getData()


if __name__ == "__main__":
    main()
