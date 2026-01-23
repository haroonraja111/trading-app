from .company_names import COMPANY_NAMES
import requests  # Import the requests library for making HTTP requests

def fetch_stock_from_psx(symbol):
    """
    Fetch live stock data from PSX Terminal API.
    """
    # If symbol is empty or None, return None immediately
    if not symbol:
        return None

    # Construct the PSX Terminal API endpoint URL using the provided stock symbol (convert to uppercase)
    url = f"https://psxterminal.com/api/ticks/REG/{symbol.upper()}"

    # Prepare HTTP headers to mimic a real browser (helps prevent being blocked by API)
    headers = {
        "User-Agent": "Mozilla/5.0",            # Identify as a Mozilla browser
        "Accept": "application/json",           # Request a JSON response
        "Referer": "https://psxterminal.com/",  # Set referer to API's main site
    }

    try:
        # Send the GET request to the API with the URL, custom headers, and a 10-second timeout
        response = requests.get(url, headers=headers, timeout=10)

        # If the response was not successful (status code is not 200 OK), return None
        if response.status_code != 200:
            return None

        # Parse the response JSON body to a Python dictionary
        payload = response.json()

        # Check (validate) if API reported success; if not, return None
        if not payload.get("success"):
            return None

        # Get the "data" field from the API payload (contains the stock info)
        data = payload.get("data")
        # If there is no data or no "price" in the data, return None
        if not data or data.get("price") is None:
            return None

        # Return a dictionary containing the relevant market info fields from API data
        return {
            "symbol": symbol,
            "name": COMPANY_NAMES.get(symbol.upper(), symbol.upper()),  # ✅ FULL NAME
            "price": data.get("price"),                # Current price of the stock
            "change": data.get("change"),              # Change in price (absolute)
            "change_percent": data.get("changePercent"), # Change in price (percent) - note capitalization
            "volume": data.get("volume"),              # Trading volume
            "high": data.get("high"),                  # Session high price
            "low": data.get("low"),                    # Session low price
        }

    # If any network, timeout, or request error occurs, print error for debugging and return None
    except requests.RequestException as e:
        print("PSX API error:", e)
        return None
