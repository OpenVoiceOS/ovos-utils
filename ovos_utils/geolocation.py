from typing import Dict, Any, Optional

import requests
from requests.exceptions import RequestException, Timeout
from timezonefinder import TimezoneFinder

from ovos_utils import timed_lru_cache
from ovos_utils.lang import standardize_lang_tag
from ovos_utils.log import LOG
from ovos_utils.network_utils import get_external_ip, is_valid_ip


_tz_finder: TimezoneFinder = None


def get_timezone(lat: float, lon: float) -> Dict[str, str]:
    """
    Determine the timezone based on latitude and longitude.

    Args:
        lat (float): Latitude in decimal degrees.
        lon (float): Longitude in decimal degrees.

    Returns:
        Dict[str, str]: A dictionary containing the timezone name and code.

    Raises:
        ValueError: If the coordinates are invalid.
        RuntimeError: If the timezone cannot be determined.
    """
    global _tz_finder
    if _tz_finder is None:
        # lazy loaded, resource intensive so we only want to do it once
        _tz_finder = TimezoneFinder()
    try:
        if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
            raise ValueError("Invalid coordinates")
        tz = _tz_finder.timezone_at(lng=lon, lat=lat)
        if not tz:
            raise RuntimeError(f"Failed to determine timezone from lat/lon: {lat}, {lon}")
        return {
            "name": tz.replace("/", " "),
            "code": tz
        }
    except ValueError as e:
        raise ValueError(f"Invalid coordinates: {str(e)}") from e
    except Exception as e:
        raise RuntimeError(f"Timezone lookup failed: {str(e)}") from e


@timed_lru_cache(seconds=600)
def get_geolocation(location: str, lang: str = "en", timeout: int = 5) -> Dict[str, Any]:
    """
    Perform geolocation lookup for a given location string.

    Args:
        location (str): The location to lookup (e.g., "Kansas City Missouri").
        lang (str): Localized city, regionName and country
        timeout (int): Timeout for the request in seconds (default is 5).

    Returns:
        Dict[str, Any]: JSON structure with lookup results.

    Raises:
        ConnectionError: If the geolocation service cannot be reached.
        ValueError: If the service returns empty results.
    """
    url = "https://nominatim.openstreetmap.org/search"
    try:
        response = requests.get(url, params={"q": location, "format": "json", "limit": 1},
                                headers={"User-Agent": "OVOS/1.0", "Accept-Language": lang}, timeout=timeout)
    except (RequestException, Timeout) as e:
        raise ConnectionError(f"Failed to connect to geolocation service: {str(e)}") from e
    if response.status_code == 200:
        results = response.json()
        if results:
            data = results[0]
        else:
            raise ValueError(f"Geolocation failed: empty result from {url}")
    else:
        # handle request failure
        raise ConnectionError(f"Geolocation failed: status code {response.status_code}")

    lat = data.get("lat")
    lon = data.get("lon")

    if lat and lon:
        return get_reverse_geolocation(lat, lon, lang)

    url = "https://nominatim.openstreetmap.org/details.php"
    try:
        response = requests.get(url, params={"osmid": data['osm_id'], "osmtype": data['osm_type'][0].upper(),
                                             "format": "json"},
                                headers={"User-Agent": "OVOS/1.0", "Accept-Language": lang}, timeout=timeout)
    except (RequestException, Timeout) as e:
        raise ConnectionError(f"Failed to connect to geolocation service: {str(e)}") from e
    if response.status_code == 200:
        details = response.json()
    else:
        # handle request failure
        raise ConnectionError(f"Geolocation failed: status code {response.status_code}")

    # if no addresstags are present for the location an empty list is sent instead of a dict
    tags = details.get("addresstags") or {}

    place_type = details.get("extratags", {}).get("linked_place") or details.get("category") or data.get(
        "type") or data.get("class")
    name = details.get("localname") or details.get("names", {}).get("name") or details.get("names", {}).get(
        "official_name") or data.get(
        "display_name", "")
    cc = details.get("country_code") or tags.get("country") or details.get("extratags", {}).get(
        'ISO3166-1:alpha2') or ""
    # TODO - lang support, official name is reported in various langs
    location = {
        "address": data["display_name"],
        "city": {
            "code": tags.get("postcode") or
                    details["calculated_postcode"] or "",
            "name": name if place_type == "city" else "",
            "state": {
                "code": tags.get("state_code") or
                        details["calculated_postcode"] or "",
                "name": name if place_type == "state" else tags.get("state"),
                "country": {
                    "code": cc.upper(),
                    "name": name if place_type == "country" else ""  # TODO - country code to name
                }
            }
        },
        "coordinate": {
            "latitude": lat,
            "longitude": lon
        }
    }
    if "timezone" not in location:
        location["timezone"] = get_timezone(lon=lon, lat=lat)
    return location


@timed_lru_cache(seconds=600)
def get_reverse_geolocation(lat: float, lon: float, lang: str = "en", timeout: int = 5) -> Dict[str, Any]:
    """
    Perform reverse geolocation lookup based on latitude and longitude.

    Args:
        lat (float): Latitude in decimal degrees.
        lon (float): Longitude in decimal degrees.
        lang (str): Localized city, regionName and country
        timeout (int): Timeout for the request in seconds (default is 5).

    Returns:
        Dict[str, Any]: JSON structure with lookup results.

    Raises:
        ConnectionError: If the reverse geolocation service cannot be reached.
        ValueError: If the service returns empty results.
    """

    url = "https://nominatim.openstreetmap.org/reverse"
    try:
        response = requests.get(url, params={"lat": lat, "lon": lon, "format": "json"},
                                headers={"User-Agent": "OVOS/1.0", "Accept-Language": lang}, timeout=timeout)
    except (RequestException, Timeout) as e:
        raise ConnectionError(f"Failed to connect to geolocation service: {str(e)}") from e

    if response.status_code == 200:
        details = response.json()
        address = details.get("address")
        if not address:
            raise ValueError(f"Reverse Geolocation failed: empty results from {url}")
    else:
        # handle request failure
        raise ConnectionError(f"Reverse Geolocation failed: status code {response.status_code}")

    location = {
        "address": details["display_name"],
        "city": {
            "code": address.get("postcode") or "",
            "name": address.get("city") or
                    address.get("village") or
                    address.get("town") or
                    address.get("hamlet") or
                    address.get("county") or "",
            "state": {
                "code": address.get("state_code") or
                        address.get("ISO3166-2-lvl4") or
                        address.get("ISO3166-2-lvl6")
                        or "",
                "name": address.get("state") or
                        address.get("county")
                        or "",
                "country": {
                    "code": address.get("country_code", "").upper() or "",
                    "name": address.get("country") or "",
                }
            }
        },
        "coordinate": {
            "latitude": details.get("lat") or lat,
            "longitude": details.get("lon") or lon
        }
    }
    if "timezone" not in location:
        location["timezone"] = get_timezone(
            lat=float(details.get("lat") or lat),
            lon=float(details.get("lon") or lon))
    return location


@timed_lru_cache(seconds=600)
def get_ip_geolocation(ip: Optional[str] = None,
                       lang: str = "en",
                       timeout: int = 5) -> Dict[str, Any]:
    """
    Perform geolocation lookup based on an IP address.

    Args:
        ip (str): The IP address to lookup.
        lang (str): Localized city, regionName and country *
        timeout (int): Timeout for the request in seconds (default is 5).

    * supported langs: ["en", "de", "es", "pt", "fr", "ja", "zh", "ru"]

    Returns:
        Dict[str, Any]: JSON structure with lookup results.

    Raises:
        ConnectionError: If the IP geolocation service cannot be reached.
        ValueError: If the service returns invalid or empty results.
    """
    if not ip or ip in ["0.0.0.0", "127.0.0.1"]:
        ip = get_external_ip()
    if not is_valid_ip(ip):
        raise ValueError(f"Invalid IP address: {ip}")

    # normalize language to expected values by ip-api.com
    lang = standardize_lang_tag(lang).split("-")[0]
    if lang not in ["en", "de", "es", "pt", "fr", "ja", "zh", "ru"]:
        LOG.warning(f"Language unsupported by ip-api.com ({lang}), defaulting to english")
        lang = "en"
    elif lang == "pt":
        lang = "pt-BR"
    elif lang == "zh":
        lang = "zh-CN"

    fields = "status,country,countryCode,region,regionName,city,lat,lon,timezone,query"
    try:
        # NOTE: ssl not available
        response = requests.get(f"http://ip-api.com/json/{ip}",
                                params={"fields": fields, "lang": lang},
                                timeout=timeout)
    except (RequestException, Timeout) as e:
        raise ConnectionError(f"Failed to connect to geolocation service: {str(e)}") from e

    if response.status_code == 200:
        data = response.json()
        if data.get("status") != "success":
            raise ValueError(f"IP geolocation failed: {data.get('message', 'Unknown error')}")
    else:
        # handle request failure
        raise ConnectionError(f"IP Geolocation failed: status code {response.status_code}")

    region_data = {"code": data["region"],
                   "name": data["regionName"],
                   "country": {
                       "code": data["countryCode"],
                       "name": data["country"]}}
    city_data = {"code": data["city"],
                 "name": data["city"],
                 "state": region_data}
    timezone_data = {"code": data["timezone"],
                     "name": data["timezone"]}
    coordinate_data = {"latitude": float(data["lat"]),
                       "longitude": float(data["lon"])}
    return {"city": city_data,
            "coordinate": coordinate_data,
            "timezone": timezone_data}
