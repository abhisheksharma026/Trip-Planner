"""
Amadeus flight pricing tool.

Fetches best available flight prices for an exact date and an optional
flex window (±N days) using the Amadeus Flight Offers Search API.

Environment variables required:
    AMADEUS_API_KEY
    AMADEUS_API_SECRET
Optional:
    AMADEUS_ENV=test|production  (defaults to test)
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx


# Simple in-memory token cache
_token_cache: Dict[str, Any] = {"token": None, "expires_at": None}


def _log(message: str) -> None:
    """Lightweight logger for debugging."""
    print(f"[amadeus_flights] {message}")


def _get_base_url() -> str:
    env = os.getenv("AMADEUS_ENV", "test").lower()
    return "https://api.amadeus.com" if env.startswith("prod") else "https://test.api.amadeus.com"


async def _get_access_token() -> str:
    """Retrieve (and cache) an OAuth token from Amadeus."""
    api_key = os.getenv("AMADEUS_API_KEY")
    api_secret = os.getenv("AMADEUS_API_SECRET")
    if not api_key or not api_secret:
        raise RuntimeError("Missing AMADEUS_API_KEY or AMADEUS_API_SECRET in environment.")

    now = datetime.now(timezone.utc)
    if _token_cache["token"] and _token_cache["expires_at"] and now < _token_cache["expires_at"]:
        return _token_cache["token"]

    base_url = _get_base_url()
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{base_url}/v1/security/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": api_key,
                "client_secret": api_secret,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        resp.raise_for_status()
        data = resp.json()
        access_token = data.get("access_token")
        expires_in = data.get("expires_in", 0)
        if not access_token:
            raise RuntimeError("Amadeus token response missing access_token.")

        _token_cache["token"] = access_token
        _token_cache["expires_at"] = now + timedelta(seconds=int(expires_in) - 60)
        return access_token


def _parse_date(date_str: str) -> datetime:
    return datetime.fromisoformat(date_str)  # Expecting YYYY-MM-DD


def _format_date(dt: datetime) -> str:
    return dt.date().isoformat()


def _parse_dt(dt_str: Optional[str]) -> Optional[datetime]:
    if not dt_str:
        return None
    # Amadeus returns ISO 8601, sometimes with Z
    if dt_str.endswith("Z"):
        dt_str = dt_str.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(dt_str)
    except Exception:
        return None


def _format_dt(dt: Optional[datetime]) -> str:
    return dt.strftime("%Y-%m-%d %H:%M") if dt else "N/A"


def _format_minutes(total_minutes: int) -> str:
    hours, minutes = divmod(int(total_minutes), 60)
    if hours and minutes:
        return f"{hours}h {minutes}m"
    if hours:
        return f"{hours}h"
    return f"{minutes}m"


def _extract_best_offer(offers: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Return the cheapest offer with a compact summary including stops and layovers."""
    if not offers:
        return None

    def _price(o: Dict[str, Any]) -> float:
        try:
            return float(o.get("price", {}).get("grandTotal", "inf"))
        except Exception:
            return float("inf")

    best = min(offers, key=_price)
    price = best.get("price", {}).get("grandTotal")
    currency = best.get("price", {}).get("currency", "")

    itineraries = best.get("itineraries", [])
    first_itin = itineraries[0] if itineraries else {}
    segments = first_itin.get("segments", [])
    first_seg = segments[0] if segments else {}
    carrier = first_seg.get("carrierCode", "N/A")
    flight_no = first_seg.get("number", "N/A")
    duration = first_itin.get("duration", "N/A")
    stops = max(len(segments) - 1, 0)

    # Collect layover airport codes and durations for transit hints
    layovers = []
    if len(segments) > 1:
        for prev_seg, next_seg in zip(segments[:-1], segments[1:]):
            arrival = prev_seg.get("arrival", {})
            departure = next_seg.get("departure", {})
            layover_code = arrival.get("iataCode")
            arr_dt = _parse_dt(arrival.get("at"))
            dep_dt = _parse_dt(departure.get("at"))
            layover_minutes = None
            if arr_dt and dep_dt:
                layover_minutes = int((dep_dt - arr_dt).total_seconds() // 60)
            layovers.append(
                {
                    "city": layover_code,
                    "arrival": _format_dt(arr_dt),
                    "departure": _format_dt(dep_dt),
                    "layover_minutes": layover_minutes,
                }
            )

    # Departure/arrival times for the full trip
    depart_dt = _parse_dt(first_seg.get("departure", {}).get("at")) if segments else None
    arrive_dt = _parse_dt(segments[-1].get("arrival", {}).get("at")) if segments else None

    return {
        "price": price,
        "currency": currency,
        "carrier": carrier,
        "flight_number": flight_no,
        "duration": duration,
        "stops": stops,
        "layovers": layovers,
        "depart_time": _format_dt(depart_dt),
        "arrive_time": _format_dt(arrive_dt),
    }


async def _fetch_offers_for_date(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str],
    currency: str,
    max_stopovers: int,
    cabin: str,
    adults: int,
) -> List[Dict[str, Any]]:
    token = await _get_access_token()
    base_url = _get_base_url()

    params = {
        "originLocationCode": origin,
        "destinationLocationCode": destination,
        "departureDate": departure_date,
        "adults": adults,
        "currencyCode": currency,
        "travelClass": cabin.upper(),
        "max": 20,
    }

    if return_date:
        params["returnDate"] = return_date
    if max_stopovers == 0:
        params["nonStop"] = "true"

    headers = {"Authorization": f"Bearer {token}"}
    _log(
        f"Fetching offers {origin}->{destination} depart={departure_date} "
        f"return={return_date or '-'} cabin={cabin} max_stopovers={max_stopovers} currency={currency}"
    )
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(f"{base_url}/v2/shopping/flight-offers", params=params, headers=headers)
        resp.raise_for_status()
        payload = resp.json()
        return payload.get("data", []) or []


async def search_flight_prices(
    origin: str,
    destination: str,
    departure_date: str,
    return_date: Optional[str] = None,
    currency: str = "USD",
    cabin: str = "ECONOMY",
    adults: int = 1,
    max_stopovers: int = 2,
    date_flex_days: int = 2,
) -> str:
    """
    Fetch best flight prices for exact dates and optional ±N-day flex window.

    Args:
        origin: Origin IATA code (e.g., BER)
        destination: Destination IATA code (e.g., PEK)
        departure_date: Departure date YYYY-MM-DD
        return_date: Optional return date YYYY-MM-DD
        currency: Currency code (default USD)
        cabin: Cabin class (ECONOMY, PREMIUM_ECONOMY, BUSINESS, FIRST)
        adults: Number of adult passengers
        max_stopovers: Maximum allowed stopovers (0 forces nonstop)
        date_flex_days: Flex window (±N days) to search for cheaper options
    """
    origin = origin.strip().upper()
    destination = destination.strip().upper()

    _log(
        f"search_flight_prices origin={origin} destination={destination} "
        f"depart={departure_date} return={return_date or '-'} flex=±{date_flex_days} "
        f"cabin={cabin} adults={adults} max_stopovers={max_stopovers} currency={currency}"
    )

    try:
        base_depart = _parse_date(departure_date)
    except Exception:
        return f"Could not parse departure_date '{departure_date}'. Please use YYYY-MM-DD."

    if return_date:
        try:
            _parse_date(return_date)
        except Exception:
            return f"Could not parse return_date '{return_date}'. Please use YYYY-MM-DD."

    try:
        exact_offers = await _fetch_offers_for_date(
            origin, destination, departure_date, return_date, currency, max_stopovers, cabin, adults
        )
        _log(f"Exact-date offers found: {len(exact_offers)}")
        exact_best = _extract_best_offer(exact_offers)
    except Exception as e:
        _log(f"Exact-date lookup failed: {e}")
        return f"Amadeus exact-date lookup failed: {e}"

    flex_best: Optional[Tuple[str, Dict[str, Any]]] = None
    searched_dates: List[str] = []

    if date_flex_days and date_flex_days > 0:
        for offset in range(-date_flex_days, date_flex_days + 1):
            flex_date = _format_date(base_depart + timedelta(days=offset))
            searched_dates.append(flex_date)
            try:
                offers = await _fetch_offers_for_date(
                    origin, destination, flex_date, return_date, currency, max_stopovers, cabin, adults
                )
                best = _extract_best_offer(offers)
                if best:
                    price = float(best["price"])
                    if not flex_best or price < float(flex_best[1]["price"]):
                        flex_best = (flex_date, best)
            except Exception as flex_err:
                _log(f"Flex-date lookup failed for {flex_date}: {flex_err}")
                continue

    lines: List[str] = []

    if exact_best:
        layover_text = ""
        if exact_best["stops"] > 0:
            layover_list = []
            for lay in exact_best.get("layovers") or []:
                if lay.get("city"):
                    duration_text = (
                        f" ({_format_minutes(lay['layover_minutes'])})"
                        if lay.get("layover_minutes") is not None
                        else ""
                    )
                    layover_list.append(f"{lay['city']}{duration_text}")
            layover_text = f" | layovers: {', '.join(layover_list)}" if layover_list else ""

        lines.append(
            f"**Exact date best price ({departure_date})**: "
            f"{exact_best['price']} {exact_best['currency']} via {exact_best['carrier']} "
            f"{exact_best['flight_number']} | duration {exact_best['duration']} | stops {exact_best['stops']}{layover_text} "
            f"| depart {exact_best.get('depart_time','N/A')} | arrive {exact_best.get('arrive_time','N/A')}"
        )
    else:
        lines.append(f"**Exact date best price ({departure_date})**: No priced offers found.")

    if flex_best:
        flex_date, best = flex_best
        flex_price = float(best["price"])
        layover_text = ""
        if best["stops"] > 0:
            layover_list = []
            for lay in best.get("layovers") or []:
                if lay.get("city"):
                    duration_text = (
                        f" ({_format_minutes(lay['layover_minutes'])})"
                        if lay.get("layover_minutes") is not None
                        else ""
                    )
                    layover_list.append(f"{lay['city']}{duration_text}")
            layover_text = f" | layovers: {', '.join(layover_list)}" if layover_list else ""
        if exact_best and exact_best.get("price"):
            exact_price = float(exact_best["price"])
            delta = flex_price - exact_price
            if delta < 0:
                rationale = f"${abs(delta):.0f} cheaper if you leave {flex_date}"
            elif delta > 0:
                rationale = f"${delta:.0f} more if you leave {flex_date}"
            else:
                rationale = f"Same price if you leave {flex_date}"
        else:
            rationale = f"Found priced option on {flex_date}"

        lines.append(
            f"**Flex window best (±{date_flex_days} days)**: "
            f"{best['price']} {best['currency']} on {flex_date} via {best['carrier']} "
            f"{best['flight_number']} | duration {best['duration']} | stops {best['stops']}{layover_text} "
            f"| depart {best.get('depart_time','N/A')} | arrive {best.get('arrive_time','N/A')} "
            f"— {rationale}"
        )
        _log(f"Flex best: {best['price']} {best['currency']} on {flex_date} — {rationale}")
    elif date_flex_days and date_flex_days > 0:
        lines.append(f"**Flex window (±{date_flex_days} days)**: No priced offers found.")

    if searched_dates:
        lines.append(f"Searched dates: {', '.join(sorted(set(searched_dates)))}")

    return "\n".join(lines)

