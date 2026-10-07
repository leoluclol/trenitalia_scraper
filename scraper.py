import time
import requests
import json
from pathlib import Path
import numpy as np
from datetime import datetime, timedelta, time as dt_time
import matplotlib.pyplot as plt

BASE = "https://www.lefrecce.it"
LANDING = f"{BASE}/Channels.Website.WEB/"
API = f"{BASE}/Channels.Website.BFF.WEB/website/ticket/solutions"

# Milano (tutte le stazioni) = 830001650
# Milano Centrale = 830001700
# Pordenone = 830002701
# Venezia Mestre = 830002589

ndays = 30
data = np.zeros((3, ndays))
dates = []
BASE_DIR = Path(__file__).resolve().parent

for i in range(ndays):
    search_date = datetime.today() + timedelta(days=1+i)
    search_date_and_time = datetime.combine(search_date.date(), dt_time(6, 0))
    iso_search_date = search_date_and_time.isoformat()
    print("Searching prices for date:", iso_search_date)

    s = requests.Session()

    s.headers.update({
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Origin": BASE,
        "Referer": LANDING,
        "X-CSRF-Token": "None",
        "channel": "41",
        "whitelabel_referrer": "www.lefrecce.it",
        "x-requested-with": "Fetch",
    })

    s.headers["callertimestamp"] = str(int(time.time() * 1000))

    payload = {
        "departureLocationId": 830002701,
        "arrivalLocationId": 830001650,
        "departureTime": iso_search_date,
        "adults": 1,
        "children": 0,
        "criteria": {
            "frecceOnly": False,
            "regionalOnly": False,
            "intercityOnly": False,
            "tourismOnly": False,
            "noChanges": True,
            "order": "CHEAPEST",
            "offset": 0,
            "limit": 10,
        },
        "advancedSearchRequest": {
            "bestFare": False,
            "bikeFilter": False,
            "forwardDiscountCodes": []
        }
    }

    stripped = {
        "solutions": []
    }

    try:
        r = s.post(API, json=payload, timeout=20)
        r.raise_for_status()
    except requests.HTTPError as exc:
        print(f"Request failed for {iso_search_date}: {exc}")
        if exc.response is not None:
            print(f"status: {exc.response.status_code}")
            print(f"content-type: {exc.response.headers.get('Content-Type', '')}")
            print(f"body preview: {exc.response.text[:300]!r}")
        r = None
    except requests.RequestException as exc:
        print(f"Request failed for {iso_search_date}: {exc}")
        r = None

    if r is not None:
        if not r.text.strip():
            print(f"Empty response body for {iso_search_date}")
        else:
            try:
                response_json = r.json()
                for item in response_json.get("solutions", []):
                    sol = item.get("solution", {})
                    trains = sol.get("trains", [])
                    price_obj = sol.get("price", {})

                    if not trains or "amount" not in price_obj:
                        continue

                    stripped["solutions"].append({
                        "departureTime": sol.get("departureTime"),
                        "arrivalTime": sol.get("arrivalTime"),
                        "duration": sol.get("duration"),
                        "price": price_obj["amount"],
                        "number": trains[0].get("name")
                    })
            except requests.exceptions.JSONDecodeError:
                content_type = r.headers.get("Content-Type", "")
                print(
                    f"Non-JSON response for {iso_search_date} "
                    f"(status={r.status_code}, content-type={content_type})."
                )
                print(f"Body preview: {r.text[:300]!r}")
    OUT = BASE_DIR / f"response_{i+1}.json"

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(stripped, f, indent=2, ensure_ascii=False)

    print(f"Saved to {OUT}")


    # Extract all prices from the stripped dictionary
    prices = [solution["price"] for solution in stripped["solutions"]]

    # Keep NaN values when no solutions are available for a day.
    if prices:
        # Convert the list of prices to a NumPy array
        prices_array = np.array(prices)

        data[0, i] = np.min(prices_array)   # min
        data[1, i] = np.mean(prices_array)  # avg
        data[2, i] = np.max(prices_array)   # max
    else:
        data[0, i] = np.nan
        data[1, i] = np.nan
        data[2, i] = np.nan

#File saving in csv format
OUT_CSV = BASE_DIR / "prices.csv"
np.savetxt(OUT_CSV, data.T, delimiter=",", header="min,avg,max", comments='', fmt="%.2f")
print(f"Saved price data to {OUT_CSV}")