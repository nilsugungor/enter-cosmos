from flask import Flask, request, jsonify, render_template
import swisseph as swe
from datetime import datetime
import pytz
from location_utils import resolve_location

app = Flask(__name__)
swe.set_ephe_path("./ephe")

SIGNS = [
    "Aries","Taurus","Gemini","Cancer","Leo","Virgo",
    "Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"
]

PLANETS = {
    "sun": swe.SUN,
    "moon": swe.MOON,
    "mercury": swe.MERCURY,
    "venus": swe.VENUS,
    "mars": swe.MARS,
    "jupiter": swe.JUPITER,
    "saturn": swe.SATURN,
    "uranus": swe.URANUS,
    "neptune": swe.NEPTUNE,
    "pluto": swe.PLUTO,
    "chiron": swe.CHIRON,
    "juno": swe.JUNO
}

def zodiac(longitude):
    sign = SIGNS[int(longitude // 30)]
    degree = longitude % 30
    return sign, round(degree, 2)

def planet_house_placidus(planet_lon, cusps):
    for i in range(12):
        start = cusps[i]
        end = cusps[(i+1)%12]
        if start < end:
            if start <= planet_lon < end:
                return i + 1
        else:  # wrap-around at 360°
            if planet_lon >= start or planet_lon < end:
                return i + 1
    return 12


def calculate_chart(date_str, time_str, city_name):
    lat, lon, tz_str = resolve_location(city_name)
    tz = pytz.timezone(tz_str)
    dt = tz.localize(datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M"))
    ut = dt.astimezone(pytz.utc)
    jd = swe.julday(ut.year, ut.month, ut.day, ut.hour + ut.minute/60)

    houses, ascmc = swe.houses(jd, lat, lon, b'P')
    asc = ascmc[0]
    asc_sign, asc_deg = zodiac(asc)

    result = {}
    result["rising"] = {"sign": asc_sign, "degree": round(asc_deg,2), "house": 1}

    # Planets
    for name, planet in PLANETS.items():
        pos = swe.calc_ut(jd, planet)
        lon_deg = pos[0][0] if isinstance(pos[0], (list, tuple)) else pos[0]
        sign, deg = zodiac(lon_deg)
        house = planet_house_placidus(lon_deg, houses)
        result[name] = {"sign": sign, "degree": deg, "house": house}

    # Regulus
    regulus = swe.fixstar_ut("Regulus", jd)
    lon_regulus = regulus[0] if isinstance(regulus[0], float) else regulus[0][0]
    sign_r, deg_r = zodiac(lon_regulus)
    house_r = planet_house_placidus(lon_regulus, houses)
    result["regulus"] = {"sign": sign_r, "degree": deg_r, "house": house_r}

    # Part of Fortune (Placidus formula)
    sun_lon = result["sun"]["degree"] + SIGNS.index(result["sun"]["sign"])*30
    moon_lon = result["moon"]["degree"] + SIGNS.index(result["moon"]["sign"])*30
    asc_deg = asc
    if sun_lon >= asc_deg and sun_lon < (asc_deg+180)%360:
        pof_lon = (asc_deg + moon_lon - sun_lon)%360
    else:
        pof_lon = (asc_deg - moon_lon + sun_lon)%360
    sign_p, deg_p = zodiac(pof_lon)
    house_p = planet_house_placidus(pof_lon, houses)
    result["part_of_fortune"] = {"sign": sign_p, "degree": deg_p, "house": house_p}

    result["city"] = city_name
    result["date"] = date_str
    return result

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/chart", methods=["POST"])
def chart():
    data = request.get_json()
    date_str = data.get("date")
    time_str = data.get("time")
    city_name = data.get("city")
    chart_data = calculate_chart(date_str, time_str, city_name)
    return jsonify(chart_data)

if __name__ == "__main__":
    app.run(debug=True)
