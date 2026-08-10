
"""Streamlit app for calculating a natal astrological chart with flatlib."""

import re
from datetime import datetime

import streamlit as st
from flatlib import aspects, const
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos

ASPECT_NAMES = {
    0: 'Conjunction',
    60: 'Sextile',
    90: 'Square',
    120: 'Trine',
    180: 'Opposition',
}
PLANETS = [
    const.SUN,
    const.MOON,
    const.MERCURY,
    const.VENUS,
    const.MARS,
    const.JUPITER,
    const.SATURN,
    const.URANUS,
    const.NEPTUNE,
    const.PLUTO,
    const.NORTH_NODE,
]


def parse_utc_offset(offset_str):
    """Validate UTC offset strings like +02:00 or -05:00."""
    pattern = r'^[+-](?:[01]\d|2[0-3]):[0-5]\d$'
    if not re.match(pattern, offset_str):
        raise ValueError('UTC offset must use the format ±HH:MM, for example +02:00 or -05:00.')
    return offset_str


def format_degree(obj):
    """Format the degree within the zodiac sign to two decimal places."""
    degree = getattr(obj, 'signlon', None)
    if degree is None:
        degree = obj.lon % 30.0
    return f'{degree:.2f}'


def build_chart(date_str, time_str, latitude, longitude, utc_offset):
    """Build a flatlib Chart object using Placidus houses."""
    date_time = Datetime(date_str, time_str, utc_offset)
    position = GeoPos(latitude, longitude)
    return Chart(date_time, position, hsys='P')


def calculate_chart(date_str, time_str, lat_str, lon_str, offset_str):
    """Validate inputs, calculate the natal chart, and return structured results."""
    date = date_str.strip()
    time = time_str.strip()
    utc_offset = parse_utc_offset(offset_str.strip())
    latitude = float(lat_str)
    longitude = float(lon_str)

    # Validate date and time formats before building the chart.
    datetime.strptime(date, '%Y/%m/%d')
    datetime.strptime(time, '%H:%M')

    chart = build_chart(date, time, latitude, longitude, utc_offset)

    asc = chart.get(const.ASC)
    mc = chart.get(const.MC)

    planets = []
    for pid in PLANETS:
        obj = chart.get(pid)
        house = chart.houses.getObjectHouse(obj)
        house_number = house.id.replace('House', '') if house is not None else 'N/A'
        planets.append(
            {
                'Planet': obj.id,
                'Sign': obj.sign,
                'Degree': format_degree(obj),
                'House': house_number,
                'Retrograde': 'Yes' if obj.isRetrograde() else 'No',
            }
        )

    houses = []
    for i in range(1, 13):
        house = chart.get(f'House{i}')
        houses.append(
            {
                'House': i,
                'Sign': house.sign,
                'Degree': format_degree(house),
            }
        )

    major_aspects = []
    aspect_ids = const.MAJOR_ASPECTS
    for i in range(len(PLANETS)):
        first = chart.get(PLANETS[i])
        for j in range(i + 1, len(PLANETS)):
            second = chart.get(PLANETS[j])
            aspect = aspects.getAspect(first, second, aspect_ids)
            if aspect.exists():
                major_aspects.append(
                    {
                        'Planet 1': first.id,
                        'Planet 2': second.id,
                        'Aspect': ASPECT_NAMES.get(aspect.type, str(aspect.type)),
                        'Orb': f'{abs(aspect.orb):.2f}°',
                    }
                )

    return {
        'ascendant': {'Sign': asc.sign, 'Degree': format_degree(asc)},
        'midheaven': {'Sign': mc.sign, 'Degree': format_degree(mc)},
        'planets': planets,
        'houses': houses,
        'aspects': major_aspects,
    }


def main():
    st.title('Natal Astrological Chart')
    st.markdown(
        'Enter birth data below and click **Calculate Chart** to generate the Ascendant, Midheaven, planet placements, house cusps, and major aspects.'
    )

    with st.form('natal-chart-form'):
        date_str = st.text_input('Birth date (YYYY/MM/DD)', value='1990/01/01')
        time_str = st.text_input('Birth time (HH:MM, 24-hour clock)', value='12:00')
        lat_str = st.text_input('Latitude (decimal degrees, e.g., 48.8566)', value='48.8566')
        lon_str = st.text_input('Longitude (decimal degrees, e.g., 2.3522)', value='2.3522')
        offset_str = st.text_input('UTC offset at birth (e.g., +02:00, -05:00)', value='+00:00')
        submitted = st.form_submit_button('Calculate Chart')

    if submitted:
        try:
            results = calculate_chart(date_str, time_str, lat_str, lon_str, offset_str)
        except ValueError as exc:
            st.error(f'Input error: {exc}')
            return
        except Exception as exc:
            st.error('Unable to compute the chart. Please verify your input values and try again.')
            st.exception(exc)
            return

        st.subheader('Ascendant and Midheaven')
        st.write(f"**Ascendant:** {results['ascendant']['Sign']} {results['ascendant']['Degree']}°")
        st.write(f"**Midheaven:** {results['midheaven']['Sign']} {results['midheaven']['Degree']}°")

        st.subheader('Planetary Positions')
        st.table(results['planets'])

        st.subheader('House Cusps')
        st.table(results['houses'])

        st.subheader('Major Aspects (5° orb)')
        if results['aspects']:
            st.table(results['aspects'])
        else:
            st.info('No major aspects were found within a 5° orb.')

    st.markdown(
        '## Run this app locally\n'
        'Use the command: `streamlit run streamlit_app.py`\n'
        'Then open the local link shown in the terminal, typically `http://localhost:8501`.'
    )


if __name__ == '__main__':
    main()
