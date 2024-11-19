import requests
from timezonefinder import TimezoneFinder

from ovos_utils import timed_lru_cache
from ovos_utils.network_utils import get_external_ip


def get_timezone(lat, lon):
    tz = TimezoneFinder().timezone_at(lng=float(lon), lat=float(lat))
    return {
        "name": tz.replace("/", " "),
        "code": tz
    }


@timed_lru_cache(seconds=600)  # cache results for 10 mins
def get_geolocation(location):
    """Call the geolocation endpoint.

    Args:
        location (str): the location to lookup (e.g. Kansas City Missouri)

    Returns:
        str: JSON structure with lookup results
    """
    url = "https://nominatim.openstreetmap.org/search"

    data = requests.get(url, params={"q": location, "format": "json", "limit": 1},
                        headers={"User-Agent": "OVOS/1.0"}).json()[0]
    lat = data.get("lat")
    lon = data.get("lon")

    if lat and lon:
        return get_reverse_geolocation(lat, lon)

    url = "https://nominatim.openstreetmap.org/details.php"
    details = requests.get(url, params={"osmid": data['osm_id'], "osmtype": data['osm_type'][0].upper(),
                                        "format": "json"},
                           headers={"User-Agent": "OVOS/1.0"}).json()

    # if no addresstags are present for the location an empty list is sent instead of a dict
    tags = details.get("addresstags") or {}

    place_type = details["extratags"].get("linked_place") or details.get("category") or data.get(
        "type") or data.get("class")
    name = details["localname"] or details["names"].get("name") or details["names"].get("official_name") or data[
        "display_name"]
    cc = details["country_code"] or tags.get("country") or details["extratags"].get('ISO3166-1:alpha2') or ""
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


@timed_lru_cache(seconds=600)  # cache results for 10 mins
def get_reverse_geolocation(lat, lon):
    """Call the reverse geolocation endpoint.

    Args:
        lat (float): latitude
        lon (float): longitude

    Returns:
        str: JSON structure with lookup results
    """
    url = "https://nominatim.openstreetmap.org/reverse"
    details = requests.get(url, params={"lat": lat, "lon": lon, "format": "json"},
                           headers={"User-Agent": "OVOS/1.0"}).json()
    address = details.get("address")
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
            lat=details.get("lat") or lat,
            lon=details.get("lon") or lon)
    return location


@timed_lru_cache(seconds=600)  # cache results for 10 mins
def get_ip_geolocation(ip):
    """Call the geolocation endpoint.

    Args:
        ip (str): the ip address to lookup

    Returns:
        str: JSON structure with lookup results
    """
    if not ip or ip in ["0.0.0.0", "127.0.0.1"]:
        ip = get_external_ip()
    fields = "status,country,countryCode,region,regionName,city,lat,lon,timezone,query"
    data = requests.get("http://ip-api.com/json/" + ip,
                        params={"fields": fields}).json()
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
