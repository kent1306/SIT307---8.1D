from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime
import csv
import json
import re

BASE = Path(__file__).resolve().parent

# Only the six verified pages are used. Incorrect/old Randwick files are intentionally excluded.
FILES = [
    ("Randwick", BASE / "1951 Houses Sold & Auction Results in Randwick, NSW, 2031 _ Domain.html", 1),
    ("Randwick", BASE / "randwick2.html", 2),
    ("Parramatta", BASE / "Parrametta1.html", 1),
    ("Parramatta", BASE / "Parramattar2.html", 2),
    ("Blacktown", BASE / "Blacktown.html", 1),
    ("Blacktown", BASE / "Blacktown2.html", 2),
]

DATE_RE = re.compile(r"(\d{1,2} [A-Za-z]{3} \d{4})$")


def parse_price(value):
    if value is None:
        return None
    digits = re.sub(r"[^0-9]", "", str(value))
    return int(digits) if digits else None


def parse_sale_info(tag_text):
    """Return ISO sale date and the sale method text from Domain's sold tag."""
    if not tag_text:
        return None, None

    tag_text = tag_text.strip()
    match = DATE_RE.search(tag_text)
    sale_date = None
    method = tag_text

    if match:
        dt = datetime.strptime(match.group(1), "%d %b %Y")
        sale_date = dt.date().isoformat()
        method = tag_text[: match.start()].strip()

    if method.lower().startswith("sold"):
        method = method[4:].strip()
    method = method or "Sold"

    return sale_date, method


def get_listings_map(html_path):
    soup = BeautifulSoup(html_path.read_text(encoding="utf-8", errors="ignore"), "html.parser")
    script = soup.find("script", id="__NEXT_DATA__")
    if script is None or not script.string:
        raise ValueError(f"Could not find __NEXT_DATA__ in {html_path.name}")

    data = json.loads(script.string)
    try:
        return data["props"]["pageProps"]["componentProps"]["listingsMap"]
    except KeyError as exc:
        raise ValueError(f"Could not find listingsMap in {html_path.name}") from exc


def extract_file(expected_suburb, html_path, page_number):
    rows = []
    listings_map = get_listings_map(html_path)

    for listing_id, wrapper in listings_map.items():
        model = wrapper.get("listingModel", {})
        address = model.get("address", {}) or {}
        features = model.get("features", {}) or {}
        tags = model.get("tags", {}) or {}

        sale_date, sale_method = parse_sale_info(tags.get("tagText"))
        land_size = features.get("landSize")
        if isinstance(land_size, (int, float)) and land_size <= 0:
            land_size = None

        relative_url = model.get("url")
        source_url = f"https://www.domain.com.au{relative_url}" if relative_url else None

        rows.append({
            "listing_id": int(listing_id) if str(listing_id).isdigit() else listing_id,
            "address": address.get("street"),
            "suburb": address.get("suburb"),
            "state": address.get("state"),
            "postcode": address.get("postcode"),
            "property_type": features.get("propertyType"),
            "bedrooms": features.get("beds"),
            "bathrooms": features.get("baths"),
            "car_spaces": features.get("parking"),
            "land_size_m2": land_size,
            "latitude": address.get("lat"),
            "longitude": address.get("lng"),
            "sale_date": sale_date,
            "sale_method": sale_method,
            "sale_price": parse_price(model.get("price")),
            "source_url": source_url,
            "source_file": html_path.name,
            "source_page": page_number,
            "expected_suburb": expected_suburb,
        })

    return rows


def write_csv(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    extracted = []
    for suburb, path, page in FILES:
        if not path.exists():
            raise FileNotFoundError(path)
        rows = extract_file(suburb, path, page)
        print(f"{suburb} page {page}: {len(rows)} listings extracted")
        extracted.extend(rows)

    # Keep the full extraction for auditability.
    raw_fields = [
        "listing_id", "address", "suburb", "state", "postcode", "property_type",
        "bedrooms", "bathrooms", "car_spaces", "land_size_m2", "latitude", "longitude",
        "sale_date", "sale_method", "sale_price", "source_url", "source_file", "source_page",
        "expected_suburb",
    ]
    write_csv(BASE / "sydney_housing_all_extracted.csv", extracted, raw_fields)

    # Clean dataset: exact suburb, exact House type, disclosed numeric price, and a sale date.
    cleaned = []
    seen_ids = set()
    for row in extracted:
        if row["suburb"] != row["expected_suburb"]:
            continue
        if row["state"] != "NSW":
            continue
        if row["property_type"] != "House":
            continue
        if row["sale_price"] is None:
            continue
        if row["sale_date"] is None:
            continue
        if row["listing_id"] in seen_ids:
            continue
        seen_ids.add(row["listing_id"])
        cleaned.append(row)

    # Sort for readability while preserving all three markets.
    cleaned.sort(key=lambda r: (r["suburb"], r["sale_date"], str(r["address"])))

    clean_fields = [
        "listing_id", "address", "suburb", "state", "postcode", "bedrooms", "bathrooms",
        "car_spaces", "land_size_m2", "latitude", "longitude", "sale_date", "sale_method",
        "sale_price", "source_url",
    ]
    write_csv(BASE / "sydney_housing_clean.csv", [{k: r.get(k) for k in clean_fields} for r in cleaned], clean_fields)

    # Compact validation report.
    suburbs = ["Randwick", "Parramatta", "Blacktown"]
    lines = []
    lines.append(f"Raw listings extracted: {len(extracted)}")
    lines.append(f"Clean unique House listings: {len(cleaned)}")
    lines.append("")
    for suburb in suburbs:
        sub = [r for r in cleaned if r["suburb"] == suburb]
        lines.append(f"{suburb}: {len(sub)} clean rows")
        for field in ["bedrooms", "bathrooms", "car_spaces", "land_size_m2", "sale_date", "sale_price"]:
            missing = sum(r.get(field) in (None, "") for r in sub)
            lines.append(f"  missing {field}: {missing}")
        if sub:
            prices = [r["sale_price"] for r in sub]
            lines.append(f"  price range: ${min(prices):,} - ${max(prices):,}")
    lines.append("")
    lines.append("Cleaning rules: exact expected suburb; NSW; exact property_type == House; numeric sale price; parsed sale date; deduplicate by listing_id.")
    lines.append("Note: land_size_m2 is retained when Domain provides a positive value; missing land size is left blank rather than imputed at collection stage.")

    report = "\n".join(lines)
    (BASE / "sydney_housing_validation.txt").write_text(report, encoding="utf-8")
    print("\n" + report)


if __name__ == "__main__":
    main()
