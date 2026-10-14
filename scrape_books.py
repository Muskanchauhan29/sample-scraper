"""
Web scraping + data cleaning pipeline.

Scrapes the book catalogue from https://books.toscrape.com (a public practice
site built for scraping), then cleans, de-duplicates and validates the data and
writes a CSV plus a short data-quality report.

Usage:
    python scrape_books.py --pages 5
"""
import argparse
import logging
import time
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://books.toscrape.com/catalogue/page-{}.html"
HEADERS = {"User-Agent": "Mozilla/5.0 (research-data-sample; contact: muskchauhan296@gmail.com)"}
RATING_MAP = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}
OUT_DIR = Path("output")

log = logging.getLogger("scraper")


def fetch(session: requests.Session, url: str, retries: int = 3, delay: float = 1.0):
    """GET a page with retries. Returns HTML text, or None if the page does not exist."""
    for attempt in range(1, retries + 1):
        try:
            resp = session.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            resp.encoding = "utf-8"  # avoids broken currency symbols
            return resp.text
        except requests.RequestException as exc:
            log.warning("Attempt %d/%d failed for %s: %s", attempt, retries, url, exc)
            time.sleep(delay * attempt)
    raise RuntimeError(f"Could not fetch {url} after {retries} attempts")


def parse_page(html: str, page_url: str, page_no: int) -> list[dict]:
    """Extract one record per book from a catalogue page."""
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for card in soup.select("article.product_pod"):
        link = card.select_one("h3 a")
        rating_tag = card.select_one("p.star-rating")
        price_tag = card.select_one("p.price_color")
        stock_tag = card.select_one("p.instock.availability")
        rows.append({
            "title": link["title"] if link and link.has_attr("title") else None,
            "price_raw": price_tag.get_text(strip=True) if price_tag else None,
            "rating_raw": next((c for c in rating_tag["class"] if c != "star-rating"), None) if rating_tag else None,
            "availability_raw": stock_tag.get_text(strip=True) if stock_tag else None,
            "url": urljoin(page_url, link["href"]) if link else None,
            "source_page": page_no,
        })
    return rows


def clean(df: pd.DataFrame):
    """Clean, de-duplicate and validate. Returns (clean_df, report dict)."""
    report = {"rows_scraped": len(df)}

    df = df.copy()
    df["title"] = df["title"].str.strip()
    df["price_gbp"] = pd.to_numeric(
        df["price_raw"].str.replace(r"[^0-9.]", "", regex=True), errors="coerce"
    )
    df["rating"] = df["rating_raw"].map(RATING_MAP)
    df["in_stock"] = df["availability_raw"].str.contains("In stock", case=False, na=False)

    # De-duplicate on the book URL (title alone can repeat for different books)
    before = len(df)
    df = df.drop_duplicates(subset="url")
    report["duplicates_removed"] = before - len(df)

    # Validate: drop rows with missing title/price/rating or out-of-range values
    valid = (
        df["title"].notna()
        & df["price_gbp"].gt(0)
        & df["rating"].between(1, 5)
    )
    report["invalid_rows_dropped"] = int((~valid).sum())
    df = df[valid]

    df = df[["title", "price_gbp", "rating", "in_stock", "url", "source_page"]].reset_index(drop=True)
    report["rows_final"] = len(df)
    report["avg_price_gbp"] = round(float(df["price_gbp"].mean()), 2) if len(df) else None
    report["avg_rating"] = round(float(df["rating"].mean()), 2) if len(df) else None
    return df, report


def main():
    parser = argparse.ArgumentParser(description="Scrape and clean the books.toscrape.com catalogue")
    parser.add_argument("--pages", type=int, default=5, help="number of catalogue pages to scrape (20 books each)")
    parser.add_argument("--delay", type=float, default=1.0, help="seconds to wait between requests")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    OUT_DIR.mkdir(exist_ok=True)

    records = []
    with requests.Session() as session:
        for page_no in range(1, args.pages + 1):
            url = BASE_URL.format(page_no)
            html = fetch(session, url)
            if html is None:
                log.info("Page %d not found, stopping.", page_no)
                break
            page_rows = parse_page(html, url, page_no)
            log.info("Page %d: %d books", page_no, len(page_rows))
            records.extend(page_rows)
            time.sleep(args.delay)  # be polite to the server

    raw = pd.DataFrame(records)
    raw.to_csv(OUT_DIR / "books_raw.csv", index=False)

    cleaned, report = clean(raw)
    cleaned.to_csv(OUT_DIR / "books_clean.csv", index=False)

    lines = ["DATA QUALITY REPORT"] + [f"{k}: {v}" for k, v in report.items()]
    (OUT_DIR / "quality_report.txt").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"\nSaved to {OUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
