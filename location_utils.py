from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

geolocator = Nominatim(user_agent="astro_app", timeout=10)
tf = TimezoneFinder()

def resolve_location(place_name):
    location = geolocator.geocode(place_name)
    if not location:
        raise ValueError("Location not found")

    lat = location.latitude
    lon = location.longitude
    tz = tf.timezone_at(lat=lat, lng=lon)

    if not tz:
        raise ValueError("Timezone not found")

    return lat, lon, tz
