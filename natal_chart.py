#!/usr/bin/env python3
"""Natal chart calculator using the flatlib astrology library."""

import re
import sys
from datetime import datetime

from flatlib import aspects, const
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import GeoPos


DATE_FORMAT = '%Y/%m/%d'
TIME_FORMAT = '%H:%M'
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
    """Parse and validate a UTC offset string like +02:00 or -05:00."""
    pattern = r'^[+-](?:[01]\d|2[0-3]):[0-5]\d$'
    if not re.match(pattern, offset_str):
        raise ValueError('UTC offset must use the format ±HH:MM, for example +02:00 or -05:00.')
    return offset_str


def format_degree(obj):
    """Return the object's degree inside its current zodiac sign."""
    degree = getattr(obj, 'signlon', None)
    if degree is None:
        degree = obj.lon % 30.0
    return f'{degree:.2f}'


def format_object_line(obj, house):
    """Format a single planet line with sign, degree, house, and retrograde state."""
    degrees = format_degree(obj)
    house_number = 'N/A'
    if house is not None and getattr(house, 'id', None):
        house_number = house.id.replace('House', '')
    retro = ' (R)' if obj.isRetrograde() else ''
    return f'{obj.id:12} {obj.sign:9} {degrees:>6}°  House {house_number:>2}{retro}'


def build_chart(date_str, time_str, latitude, longitude, utc_offset):
    """Create a flatlib Chart object for the specified birth data."""
    date_time = Datetime(date_str, time_str, utc_offset)
    position = GeoPos(latitude, longitude)
    return Chart(date_time, position, hsys='P')


def main():
    print('Natal Chart Calculator')
    print('Please enter birth information using the requested formats.')

    date_str = input('Birth date (YYYY/MM/DD): ').strip()
    time_str = input('Birth time (HH:MM, 24-hour clock): ').strip()
    lat_str = input('Latitude (decimal degrees, e.g., 48.8566): ').strip()
    lon_str = input('Longitude (decimal degrees, e.g., 2.3522): ').strip()
    offset_str = input('UTC offset at birth (e.g., +02:00, -05:00): ').strip()

    try:
        datetime.strptime(date_str, DATE_FORMAT)
        datetime.strptime(time_str, TIME_FORMAT)
        latitude = float(lat_str)
        longitude = float(lon_str)
        utc_offset = parse_utc_offset(offset_str)
    except ValueError as exc:
        print('\nInvalid input. Please use the requested formats:')
        print(' - Date: YYYY/MM/DD')
        print(' - Time: HH:MM (24-hour)')
        print(' - UTC offset: ±HH:MM')
        print(f'Error details: {exc}')
        sys.exit(1)

    try:
        chart = build_chart(date_str, time_str, latitude, longitude, utc_offset)
    except Exception as exc:
        print('\nUnable to build the natal chart. Please verify your data and try again.')
        print(f'Error details: {exc}')
        sys.exit(1)

    print('\nChart Points')
    asc = chart.get(const.ASC)
    mc = chart.get(const.MC)
    print(f'Ascendant: {asc.sign} {format_degree(asc)}°')
    print(f'Midheaven: {mc.sign} {format_degree(mc)}°')

    print('\nPlanets')
    for planet_id in PLANETS:
        planet = chart.get(planet_id)
        house = chart.houses.getObjectHouse(planet)
        print(format_object_line(planet, house))

    print('\nHouse Cusps')
    for house_num in range(1, 13):
        house = chart.get(f'House{house_num}')
        print(f'House {house_num:2}: {house.sign:9} {format_degree(house)}°')

    print('\nMajor Aspects (orb 5°)')
    found_aspect = False
    aspect_ids = const.MAJOR_ASPECTS
    for i in range(len(PLANETS)):
        first = chart.get(PLANETS[i])
        for j in range(i + 1, len(PLANETS)):
            second = chart.get(PLANETS[j])
            aspect = aspects.getAspect(first, second, aspect_ids)
            if aspect.exists():
                aspect_name = ASPECT_NAMES.get(aspect.type, str(aspect.type))
                print(f'{first.id:12} - {second.id:12} {aspect_name:10} orb {abs(aspect.orb):.2f}°')
                found_aspect = True

    if not found_aspect:
        print('No major aspects were found within the 5° orb.')


if __name__ == '__main__':
    main()
