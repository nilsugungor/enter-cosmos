# Enter Cosmos: Personal Astrology Engine

Enter Cosmos is a high-precision and fun astrology engine that generates detailed natal charts and PDF reports using the **Swiss Ephemeris**.

## Features
- **Precise Calculations:** Uses the `pyswisseph` library for professional-grade planetary positions.
- **Dynamic Interpretations:** Custom logic to interpret planets in signs and houses.
- **PDF Export:** Generates a beautifully styled, cosmic-themed PDF report of your "Cosmic Blueprint."
- **Responsive Web UI:** A minimalist, interface designed for an immersive experience.

<p align="center">
  <img src="screenshots/preview.png" width="400" alt="Astrology PDF report preview">
</p>

## Tech Stack
- **Backend:** Python / Flask
- **Frontend:** HTML5, CSS3 (Custom Ink-Blue Theme), JavaScript
- **Astrology Engine:** Swiss Ephemeris (`pyswisseph`)
- **PDF Engine:** ReportLab
- **Deployment:** Vercel
- **Location:** Geopy (Nominatim), TimezoneFinder, Pytz

## Project Structure
- app.py: Main Flask application and PDF logic.
- ephe/: Swiss Ephemeris data files (.se1).
- data/: JSON files containing interpretations and cosmic texts.
- location_utils.py: Geocoding and timezone resolution.
- static/: CSS and JS files.
- templates/: HTML templates.

## A Note on Location Search (UX)
- The city search (location autocomplete) feature uses the Nominatim (OpenStreetMap) free API.
- Latency: You might experience a slight delay (approx. 1 second) when typing in the location field. This is due to the rate-limiting and response times of the free geocoding service.
- Accuracy: For the best results, wait for the dropdown menu to appear and select your city from the list to ensure the correct coordinates are passed to the cosmic engine.
- Future improvement: Integration with a paid Google Maps or Mapbox API for faster autocomplete.

## Swiss Ephemeris Data Files
- seas_18.se1 (Main Ephemeris): Provides core data for planetary positions between 1800 AD and 2400 AD. This ensures millimetric accuracy for all modern natal charts.
- sepl_18.se1 (Planetary Data): Contains orbital data for planets from Mercury to Pluto. It is the backbone for calculating planetary degrees and sign placements.
- semo_18.se1 (Lunar Data): Specifically designed to handle the Moon's complex orbital path. This allows for the precise calculation of the Moon sign and its house placement.
- sefstars.se1 (Fixed Stars): Includes positional data for major fixed stars. In this project, it is specifically used to calculate the position of Regulus.

## License
- This project is for personal use and portfolio purposes. Data from Swiss Ephemeris is subject to their own licensing terms.
