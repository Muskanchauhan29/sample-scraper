"""Offline test of the parsing and cleaning logic using a small mock HTML page.

This checks the logic only. It does not scrape the live site.
Run: python test_parser.py
"""
import pandas as pd

from scrape_books import clean, parse_page

MOCK_HTML = """
<html><body><ol>
<li><article class="product_pod">
  <p class="star-rating Three"></p>
  <h3><a href="a-light-in-the-attic_1000/index.html" title="A Light in the Attic">A Light in ...</a></h3>
  <div class="product_price"><p class="price_color">£51.77</p>
  <p class="instock availability"><i class="icon-ok"></i> In stock</p></div>
</article></li>
<li><article class="product_pod">
  <p class="star-rating One"></p>
  <h3><a href="tipping-the-velvet_999/index.html" title="Tipping the Velvet">Tipping ...</a></h3>
  <div class="product_price"><p class="price_color">£53.74</p>
  <p class="instock availability"><i class="icon-ok"></i> In stock</p></div>
</article></li>
<li><article class="product_pod">
  <p class="star-rating Three"></p>
  <h3><a href="a-light-in-the-attic_1000/index.html" title="A Light in the Attic">A Light in ...</a></h3>
  <div class="product_price"><p class="price_color">£51.77</p>
  <p class="instock availability"><i class="icon-ok"></i> In stock</p></div>
</article></li>
<li><article class="product_pod">
  <h3><a href="broken_1/index.html" title="Broken Row">Broken ...</a></h3>
  <div class="product_price"><p class="price_color">£0.00</p></div>
</article></li>
</ol></body></html>
"""


def test_parse_and_clean():
    rows = parse_page(MOCK_HTML, "https://books.toscrape.com/catalogue/page-1.html", 1)
    assert len(rows) == 4, "should find 4 product cards"

    df, report = clean(pd.DataFrame(rows))
    assert report["rows_scraped"] == 4
    assert report["duplicates_removed"] == 1, "same URL appears twice"
    assert report["invalid_rows_dropped"] == 1, "row with no rating and zero price is invalid"
    assert report["rows_final"] == 2
    assert df["price_gbp"].tolist() == [51.77, 53.74]
    assert df["rating"].tolist() == [3, 1]
    assert df["in_stock"].all()
    print("All checks passed.")
    print(report)


if __name__ == "__main__":
    test_parse_and_clean()
