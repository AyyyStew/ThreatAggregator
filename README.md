# Threat Aggregator
## Process
1. Gather bulk malicious IPs and IoC from internet threat feeds.
2. Normalize and store the data locally
3. Create API to view aggregate data
4. Create API to download bulk data
5. Create scheduled job to periodically pull new data from threat feeds
6. Update local data with new data

## Sources of Indicators
Will start out with just finding malicious IPs
- [Emerging Threats](https://rules.emergingthreats.net/open/suricata/)
- [URLHaus](https://urlhaus.abuse.ch/api/)
- [FeodoTracker](https://feodotracker.abuse.ch/blocklist/#iocs)

## Technologies and Rationale
**Storage**: SQLite

Simple, Easy to setup, Familiarity

**Web Framework**: FastAPI (Python)

Familiarity, Easy to use, Type system
