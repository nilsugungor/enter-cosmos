import swisseph as swe
from datetime import datetime
import pytz

# tell Swiss Ephemeris where the ephemeris files are
swe.set_ephe_path("./ephe")

# helper to convert longitude to zodiac sign
SIGNS = [
    "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
    "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"
]

def zodiac(longitude):
    sign = SIGNS[int(longitude // 30)]
    degree = longitude % 30
    return sign, round(degree, 2)

# --- set birth date/time ---
# example: June 15, 1990 at 14:30 UTC
dt = pytz.utc.localize(datetime(1990, 6, 15, 14, 30))

# Julian Day
jd = swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60)

# --- Sun ---
sun = swe.calc_ut(jd, swe.SUN)
s_sign, s_deg = zodiac(sun[0][0])
print(f"Sun: {s_deg}° {s_sign}")

# --- Moon ---
moon = swe.calc_ut(jd, swe.MOON)
m_sign, m_deg = zodiac(moon[0][0])
print(f"Moon: {m_deg}° {m_sign}")

# --- Rising sign (Ascendant) ---
# example location: New York City
lat = 40.7128
lon = -74.0060
houses, ascmc = swe.houses(jd, lat, lon)
asc = ascmc[0]
a_sign, a_deg = zodiac(asc)
print(f"Rising: {a_deg}° {a_sign}")

# --- Regulus (fixed star) ---
regulus = swe.fixstar_ut("Regulus", jd)

# get longitude safely
longitude = regulus[0] if isinstance(regulus[0], float) else regulus[0][0]

r_sign, r_deg = zodiac(longitude)
print(f"Regulus: {r_deg}° {r_sign}")
