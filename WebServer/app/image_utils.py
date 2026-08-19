import os
import requests
from PIL.ExifTags import TAGS, GPSTAGS

from .utils import get_decimal_from_dms

user_agent = os.environ["USER_AGENT"]

def get_date_text(exif_data):
    datetime = exif_data.get(36867) or exif_data.get(306)
    date = datetime.split(" ")[0].split(":")
    date_string = "/".join([date[1], date[2], date[0]])

    return date_string

def get_location_text(exif_data):
    GPSINFO_TAG = next(
        tag for tag, name in TAGS.items() if name == "GPSInfo"
    )

    gps_info = {}
    for key in exif_data.get_ifd(GPSINFO_TAG):
        sub_tag_name = GPSTAGS.get(key, key)
        gps_info[sub_tag_name] = exif_data.get_ifd(GPSINFO_TAG)[key]

    if not gps_info:
        return ""

    lat = get_decimal_from_dms(gps_info['GPSLatitude'], gps_info['GPSLatitudeRef'])
    lon = get_decimal_from_dms(gps_info['GPSLongitude'], gps_info['GPSLongitudeRef'])

    payload = {"lat": lat, "lon": lon, "format": "jsonv2"}
    headers = {"User-Agent": user_agent}
    req = requests.request("GET","https://nominatim.openstreetmap.org/reverse", params=payload, headers=headers)
    geo_data = req.json()

    if (req.status_code == requests.codes.ok):
        city = str(geo_data["address"].get("city"))
        if not city:
            city = str(geo_data["address"].get("village"))
        country = str(geo_data["address"]["country"])
        if (city == "New York"):
            suburb = str(geo_data["address"]["suburb"])
            return suburb + ", NY"
        elif (country == "United States"):
            state = str(geo_data["address"]["state"])
            return city + ", " + state
        else:
            return city + ", " + country
    return ""
