# Web Scraping and Data Cleaning Sample

A Python pipeline that collects data from a public website, then cleans, de-duplicates and validates it.

**Source:** [books.toscrape.com](https://books.toscrape.com), a public practice site built for scraping.

## What it does

1. Fetches catalogue pages with `requests`, using a session, retries, a polite delay between requests and a clear User-Agent.
2. Parses each book (title, price, star rating, availability, URL) with `BeautifulSoup`.
3. Cleans the data: strips currency symbols, converts word ratings ("Three") to numbers, converts availability to True/False.
4. De-duplicates on the book URL.
5. Validates each row (title present, price above zero, rating between 1 and 5) and drops invalid rows.
6. Writes `books_raw.csv`, `books_clean.csv` and a `quality_report.txt` with row counts at each step.

## Run it

```bash
pip install -r requirements.txt
python scrape_books.py --pages 5      # 5 pages = 100 books
python test_parser.py                 # offline test of the parsing and cleaning logic
```

Output is saved in the `output/` folder.

## Files

| File | Purpose |
| --- | --- |
| `scrape_books.py` | Scraper and cleaning pipeline |
| `test_parser.py` | Offline test on mock HTML |
| `requirements.txt` | Dependencies |
| `output/books_clean.csv` | Cleaned dataset |
| `output/quality_report.txt` | Rows scraped, duplicates removed, invalid rows dropped |

## Adapting it

The same structure (fetch, parse, clean, validate, report) applies to other public sources. Only the URL pattern and the CSS selectors in `parse_page` need to change.
