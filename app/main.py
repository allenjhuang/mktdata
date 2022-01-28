import bs4
from dotenv import load_dotenv
from flask import Flask, jsonify
import requests
import os

load_dotenv()

VALID_KINDS = {
    "volume": ("vol", "volume"),
    "open_interest": ("oi", "openinterest", "open_interest"),
}
VALID_DAY_RANGES = (10, 20, 30, 60, 90, 120, 180)

app = Flask(__name__)


@app.route("/pcr/<kind>/<symbol_str>/<int:day_range>", methods=["GET"])
def get_pcr_route(kind, symbol_str, day_range):
    result = get_pcr(kind.lower(), symbol_str, day_range)
    if result == "--":
        "error: data is not available from alphaquery"
    return result


@app.route("/er/<symbol_str>", methods=["GET"])
def get_er_route(symbol_str: str):
    return get_er(symbol_str)


@app.route("/fgi", methods=["GET"])
def get_fgi_route():
    return (
        get_fgi(),
        200,
        {"Content-Type": "application/json"},
    )


def get_pcr(kind: str, symbol_str: str, day_range: int) -> str:
    """Returns the put-call ratio for the symbol."""
    if kind not in VALID_KINDS["volume"] and kind not in VALID_KINDS["open_interest"]:
        return "error: invalid kind"
    if day_range not in VALID_DAY_RANGES:
        return "error: invalid day range"
    url = f"https://www.alphaquery.com/stock/{symbol_str}/volatility-option-statistics/{day_range}-day/put-call-ratio-oi"
    html = requests.get(url).text
    soup = bs4.BeautifulSoup(html, "html.parser")
    if kind in VALID_KINDS["volume"]:
        tag_id = "indicator-put-call-ratio-volume"
    elif kind in VALID_KINDS["open_interest"]:
        tag_id = "indicator-put-call-ratio-oi"
    query = f"tr[id={tag_id}] div[class=indicator-figure-inner]"
    matching_tag_elements = soup.select(query)
    if len(matching_tag_elements) == 0:
        return "error: invalid symbol"
    pcr_str = matching_tag_elements[0].contents[0]
    return pcr_str


def get_er(symbol_str: str) -> str:
    """Returns the expense ratio for the symbol."""
    url = f"https://finance.yahoo.com/quote/{symbol_str}"
    html = requests.get(url).text
    soup = bs4.BeautifulSoup(html, "html.parser")
    query = "div[id=quote-summary] td[data-test=EXPENSE_RATIO-value]"
    matching_tag_elements = soup.select(query)
    if len(matching_tag_elements) == 0:
        return "error: symbol not found or expense ratio not found for symbol"
    er_str = matching_tag_elements[0].contents[0][:-1]
    return er_str


def get_fgi() -> str:
    """Returns the CNN fear and greed index as a string in JSON format."""
    url = "https://fear-and-greed-index.p.rapidapi.com/v1/fgi"
    headers = {
        "x-rapidapi-host": "fear-and-greed-index.p.rapidapi.com",
        "x-rapidapi-key": os.environ["RAPIDAPI_KEY"],
    }
    response = requests.get(url, headers=headers)
    fgi_str = response.text
    return fgi_str


if __name__ == "__main__":
    app.run(host="localhost", port=5000, debug=True)
