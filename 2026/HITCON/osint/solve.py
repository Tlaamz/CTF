#!/usr/bin/env python3
"""Reproduce the local Plus Code candidates; Python standard library only."""

import argparse
from decimal import Decimal
from math import cos, hypot, radians


D = Decimal
ALPHABET = "23456789CFGHJMPQRVWX"
RESOLUTIONS = tuple(map(D, ("20", "1", ".05", ".0025", ".000125")))
CELL = RESOLUTIONS[-1]
PANORAMA = (D("-43.9853387"), D("170.4650508"))

# The manually chosen priority order from the investigation, as offsets from
# the panorama's cell: (north, east). This is a heuristic, not an image matcher.
PRIORITY = (
    (0, 1), (1, 1), (1, 0), (0, 2), (1, 2),
    (-1, 2), (0, -1), (1, -1), (-1, -1),
    (-2, 0), (-2, 1), (-2, 2), (-2, -1),
    (2, 0), (2, 1), (2, 2), (2, -1),
    (0, -2), (1, -2), (-1, -2), (-2, -2), (2, -2),
)


def encode(latitude, longitude):
    """Encode a coordinate as a full 10-digit Plus Code (8 digits + 2)."""
    latitude, longitude = D(str(latitude)), D(str(longitude))
    if not (D(-90) <= latitude < D(90)):
        raise ValueError("Latitude must be in [-90, 90).")
    if not (D(-180) <= longitude < D(180)):
        raise ValueError("Longitude must be in [-180, 180).")

    values = [latitude + 90, longitude + 180]
    characters = []
    for resolution in RESOLUTIONS:
        for axis in range(2):
            digit = int(values[axis] // resolution)
            characters.append(ALPHABET[digit])
            values[axis] -= digit * resolution
    code = "".join(characters)
    return code[:8] + "+" + code[8:]


def decode(code):
    """Return the cell's south, west, north and east boundaries in degrees."""
    code = code.upper()
    if len(code) != 11 or code[8] != "+":
        raise ValueError("Expected a full Plus Code in XXXXXXXX+XX form.")
    digits = code[:8] + code[9:]
    if any(character not in ALPHABET for character in digits):
        raise ValueError("Invalid Plus Code character.")
    south, west = D(-90), D(-180)
    for i, resolution in enumerate(RESOLUTIONS):
        south += ALPHABET.index(digits[2 * i]) * resolution
        west += ALPHABET.index(digits[2 * i + 1]) * resolution
    if not (D(-90) <= south < D(90) and D(-180) <= west < D(180)):
        raise ValueError("Plus Code is outside the geographic coordinate range.")
    return south, west, south + CELL, west + CELL


def neighbour(north_offset, east_offset):
    south, west, _, _ = decode(encode(*PANORAMA))
    latitude = south + (D(north_offset) + D(".5")) * CELL
    longitude = west + (D(east_offset) + D(".5")) * CELL
    return encode(latitude, longitude)


def inspect(code):
    south, west, north, east = decode(code)
    latitude, longitude = (south + north) / 2, (west + east) / 2
    earth_radius = 6371008.8
    north_metres = earth_radius * radians(float(latitude - PANORAMA[0]))
    east_metres = earth_radius * cos(radians(float(PANORAMA[0]))) * radians(
        float(longitude - PANORAMA[1])
    )
    print(f"Code: {code.upper()}")
    print(f"South: {south:.6f}")
    print(f"North: {north:.6f}")
    print(f"West: {west:.6f}")
    print(f"East: {east:.6f}")
    print(f"Center: {latitude:.7f}, {longitude:.7f}")
    print(f"Offset from panorama: north {north_metres:.1f} m, east {east_metres:.1f} m")
    print(f"Approximate distance: {hypot(north_metres, east_metres):.1f} m")
    print(f"Google Maps: https://www.google.com/maps?q={latitude:.7f},{longitude:.7f}")
    print(f"Flag: hitcon{{{code.upper()}}}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    options = parser.add_mutually_exclusive_group()
    options.add_argument("--grid", action="store_true", help="Print all 25 cells, north first.")
    options.add_argument("--encode", nargs=2, metavar=("LAT", "LON"))
    options.add_argument("--inspect", metavar="CODE", help="Decode a full 10-digit Plus Code.")
    args = parser.parse_args()

    if args.grid:
        for north in range(2, -3, -1):
            print(" ".join(neighbour(north, east) for east in range(-2, 3)))
    elif args.encode:
        print(encode(*args.encode))
    elif args.inspect:
        inspect(args.inspect)
    else:
        for north, east in PRIORITY:
            print(f"hitcon{{{neighbour(north, east)}}}")


if __name__ == "__main__":
    main()
