from flask import Flask, request, jsonify, render_template, send_file
import swisseph as swe
from datetime import datetime
import pytz
import json
import os
from io import BytesIO
from location_utils import resolve_location

#pdf export modules
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable


#dynamic path for vercel
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EPHE_PATH = os.path.join(BASE_DIR, 'ephe')

os.environ['SE_EPHE_PATH'] = EPHE_PATH

app = Flask(__name__)

def load_json(filename):
    full_path = os.path.join(BASE_DIR, filename)
    if os.path.exists(full_path):
        with open(full_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

#loading data from base_dir
planet_sign_text = load_json("data/planet_sign_text.json")
planet_house_text = load_json("data/planet_house_text.json")

SIGNS = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]

PLANETS = {
    "sun": swe.SUN, "moon": swe.MOON, "mercury": swe.MERCURY, "venus": swe.VENUS,
    "mars": swe.MARS, "jupiter": swe.JUPITER, "saturn": swe.SATURN, "uranus": swe.URANUS,
    "neptune": swe.NEPTUNE, "pluto": swe.PLUTO, "chiron": swe.CHIRON, "juno": swe.JUNO
}

ELEMENTS_MAP = {
    "Fire": ["Aries", "Leo", "Sagittarius"],
    "Earth": ["Taurus", "Virgo", "Capricorn"],
    "Air": ["Gemini", "Libra", "Aquarius"],
    "Water": ["Cancer", "Scorpio", "Pisces"]
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
            if start <= planet_lon < end: return i + 1
        else:
            if planet_lon >= start or planet_lon < end: return i + 1
    return 12

def get_element_analysis(chart_data):
    counts = {"Fire": 0, "Earth": 0, "Air": 0, "Water": 0}
    core_keys = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "rising"]
    for key in core_keys:
        if key in chart_data:
            sign = chart_data[key]["sign"]
            for element, signs in ELEMENTS_MAP.items():
                if sign in signs: counts[element] += 1
    total = sum(counts.values())
    if total == 0: return counts
    return {k: round((v / total) * 100) for k, v in counts.items()}

def calculate_chart(date_str, time_str, city_name):
    #ephemeris path
    swe.set_ephe_path(EPHE_PATH)

    lat, lon, tz_str = resolve_location(city_name)
    tz = pytz.timezone(tz_str)
    dt = tz.localize(datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M"))
    ut = dt.astimezone(pytz.utc)
    jd = swe.julday(ut.year, ut.month, ut.day, ut.hour + ut.minute/60)

    houses, ascmc = swe.houses(jd, lat, lon, b'P')
    asc = ascmc[0]
    asc_sign, asc_deg = zodiac(asc)

    result = {"rising": {"sign": asc_sign, "degree": round(asc_deg,2), "house": 1}}

    for name, planet in PLANETS.items():
        pos = swe.calc_ut(jd, planet)
        lon_deg = pos[0][0] if isinstance(pos[0], (list, tuple)) else pos[0]
        sign, deg = zodiac(lon_deg)
        result[name] = {"sign": sign, "degree": deg, "house": planet_house_placidus(lon_deg, houses)}

    # Regulus + Part of Fortune
    reg_data = swe.fixstar_ut("Regulus", jd)
    lon_reg = reg_data[0] if isinstance(reg_data[0], float) else reg_data[0][0]
    result["regulus"] = {"sign": zodiac(lon_reg)[0], "degree": zodiac(lon_reg)[1], "house": planet_house_placidus(lon_reg, houses)}

    sun_pos = swe.calc_ut(jd, swe.SUN)[0]
    sun_lon = sun_pos[0] if isinstance(sun_pos, (list, tuple)) else sun_pos
    moon_pos = swe.calc_ut(jd, swe.MOON)[0]
    moon_lon = moon_pos[0] if isinstance(moon_pos, (list, tuple)) else moon_pos
    is_day = 7 <= planet_house_placidus(sun_lon, houses) <= 12
    pof_lon = (asc + moon_lon - sun_lon) % 360 if is_day else (asc + sun_lon - moon_lon) % 360
    result["part_of_fortune"] = {"sign": zodiac(pof_lon)[0], "degree": zodiac(pof_lon)[1], "house": planet_house_placidus(pof_lon, houses)}

    return result

#routes
@app.route("/")
def index(): 
    return render_template("index.html")

@app.route("/chart", methods=["POST"])
def chart():
    data = request.get_json()
    c_data = calculate_chart(data.get("date"), data.get("time"), data.get("city"))
    e_data = get_element_analysis(c_data)
    return jsonify({"chart": c_data, "elements": e_data})

@app.route("/interpretations")
def interpretations(): 
    return jsonify({"planet_sign": planet_sign_text, "planet_house": planet_house_text})

#pdf generation
def draw_background(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(colors.HexColor("#050505"))
    canvas.rect(0, 0, letter[0], letter[1], fill=1)
    
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.HexColor("#666666"))
    footer_text = "Generated by Nilsu Gungor | https://enter-cosmos.vercel.app/"
    canvas.drawCentredString(letter[0]/2, 30, footer_text)
    canvas.restoreState()

@app.route("/export-pdf", methods=["POST"])
def export_pdf():
    input_data = request.get_json()
    chart = input_data.get('chart', {})
    user = input_data.get('user', {})
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=65, rightMargin=65, topMargin=60, bottomMargin=60)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('Title', fontSize=32, textColor=colors.HexColor("#9b59b6"), alignment=1, fontName="Helvetica-Bold", spaceAfter=25, leading=38)
    sub_header_style = ParagraphStyle('SubHeader', fontSize=10, textColor=colors.HexColor("#d8b2ff"), alignment=1, spaceAfter=15, leading=14)
    planet_label = ParagraphStyle('PlanetLabel', fontSize=18, textColor=colors.HexColor("#9b59b6"), fontName="Helvetica-Bold", spaceBefore=35, spaceAfter=12, leading=22)
    info_style = ParagraphStyle('InfoStyle', fontSize=11, textColor=colors.HexColor("#d8b2ff"), fontName="Helvetica-Oblique", spaceAfter=20, leading=14)
    body_text = ParagraphStyle('BodyText', fontSize=10, textColor=colors.HexColor("#eeeeee"), leading=16, spaceAfter=12)

    elements = [Paragraph("ENTER COSMOS", title_style)]
    elements.append(Paragraph(f"REPORT FOR: {user.get('city', '').upper()}", sub_header_style))
    elements.append(Paragraph(f"{user.get('date', '')} | {user.get('time', '')}", sub_header_style))
    elements.append(Spacer(1, 30))

    manual_names = {"sun": "Sun", "moon": "Moon", "mercury": "Mercury", "venus": "Venus", "mars": "Mars", "jupiter": "Jupiter", "saturn": "Saturn", "uranus": "Uranus", "neptune": "Neptune", "pluto": "Pluto", "chiron": "Chiron", "juno": "Juno", "rising": "Rising", "part_of_fortune": "Part of Fortune", "regulus": "Regulus"}
    order = ["sun","moon","rising","mercury","venus","mars","jupiter","saturn","uranus","neptune","pluto","chiron","part_of_fortune","regulus","juno"]

    for key in order:
        if key not in chart: continue
        val = chart[key]
        json_key = manual_names.get(key, key.capitalize())
        elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#3d214d"), spaceBefore=10, spaceAfter=10))
        elements.append(Paragraph(f"{json_key.upper()} IN {val['sign'].upper()}", planet_label))
        elements.append(Paragraph(f"{val['house']}. House • {val['degree']}° Position", info_style))
        s_txt = planet_sign_text.get(json_key, {}).get(val['sign'], "Decoding...")
        elements.append(Paragraph(s_txt, body_text))
        h_txt = planet_house_text.get(json_key, {}).get(str(val['house']), "")
        if h_txt: elements.append(Paragraph(h_txt, body_text))

    doc.build(elements, onFirstPage=draw_background, onLaterPages=draw_background)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="enter-cosmos.pdf", mimetype='application/pdf')

if __name__ == "__main__":
    app.run(debug=True)