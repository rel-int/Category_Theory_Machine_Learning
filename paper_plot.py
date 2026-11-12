"""
Plot the cumulative number of papers listed in README.md over time.

Every paper in README.md needs a row in dates.csv, keyed by the paper's
(first) link, with the date it first appeared publicly:

    url,date,source

`date` is YYYY-MM, or YYYY when the month is unknown (plotted mid-year).
`source` says where the date comes from (e.g. "arXiv ID", a venue or a
thesis title page) so it can be checked later.

Run with --check to only validate dates.csv against README.md.
"""

import csv
import re
import sys

README = "README.md"
DATES = "dates.csv"
OUTPUT = "ct_intersection_ml.png"

# Sections whose entries are not papers and so are not plotted.
EXCLUDED_SECTIONS = {"Blog posts"}

ENTRY = re.compile(r"^\s*\* \[[^\]]*\]\(([^)\s]+)\)")
SECTION = re.compile(r"^###\s+(.*\S)")
ARXIV = re.compile(r"arxiv\.org/abs/(\d{2})(\d{2})\.\d+")
DATE = re.compile(r"^(\d{4})(?:-(0[1-9]|1[0-2]))?$")


def readme_urls():
    section, urls = None, []
    for line in open(README, encoding="utf-8"):
        if m := SECTION.match(line):
            section = m.group(1)
        elif (m := ENTRY.match(line)) and section not in EXCLUDED_SECTIONS:
            urls.append(m.group(1))
    return urls


def load_dates():
    dates, errors = {}, []
    with open(DATES, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            url, date = row["url"], row["date"]
            if not DATE.match(date):
                errors.append(f"bad date {date!r} for {url} (want YYYY-MM or YYYY)")
            if url in dates:
                errors.append(f"duplicate row for {url}")
            dates[url] = date
    return dates, errors


def to_year(date):
    year, month = DATE.match(date).groups()
    return int(year) + ((int(month) - 1) / 12 if month else 0.5)


def check():
    urls = readme_urls()
    dates, errors = load_dates()
    for url in urls:
        if url not in dates:
            hint = ""
            if m := ARXIV.search(url):
                hint = f" (suggested row: {url},20{m.group(1)}-{m.group(2)},arXiv ID)"
            errors.append(f"no date in {DATES} for {url}{hint}")
    for url in sorted(set(dates) - set(urls)):
        errors.append(f"{DATES} has a row for {url}, which is not a paper in {README}")
    if errors:
        sys.exit("\n".join(errors))
    return [to_year(dates[url]) for url in urls]


def plot(data):
    import math
    import matplotlib.pyplot as plt

    start, end = math.floor(min(data)), math.ceil(max(data) + 1 / 12)
    plt.rcParams["figure.figsize"] = (14.4, 8.34)
    plt.hist(data, bins=12 * (end - start), range=(start, end), cumulative=True)
    plt.xticks(range(start, end + 1, 2))
    plt.title("CT ∩ ML: Cumulative number of papers through time", fontsize=22)
    plt.xlabel("Year", fontsize=20)
    plt.ylabel("Total number of papers", fontsize=20)
    plt.tick_params(axis="both", which="major", labelsize=18)
    plt.savefig(OUTPUT, dpi=100)


if __name__ == "__main__":
    data = check()
    print(f"{len(data)} papers dated, earliest {min(data):.2f}, latest {max(data):.2f}")
    if "--check" not in sys.argv:
        plot(data)
