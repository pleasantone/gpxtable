import pytest
from datetime import datetime, timedelta, timezone
from io import StringIO
from typing import Tuple

from gpxpy.gpx import (
    GPX,
    GPXRoute,
    GPXRoutePoint,
    GPXTrackSegment,
    GPXTrackPoint,
    GPXTrack,
    GPXWaypoint,
)
from gpxpy.geo import Location
from gpxtable.gpxtable import (
    GPXTableCalculator,
    GPXTrackExt,
    GPXWaypointExt,
)


@pytest.fixture
def gpx_data() -> Tuple[GPX, StringIO]:
    gpx = GPX()
    gpx.author_name = "John Doe"
    gpx.author_email = "unittest@example.com"
    gpx.creator = "Unit Test Creator"
    gpx.description = "Unit Test Description"
    gpx.name = "Unit Test GPX Name"

    track = GPXTrack(
        name="Unit Test Track Name", description="Unit Test Track Description"
    )
    segment = GPXTrackSegment()
    segment.points.extend(
        [
            GPXTrackPoint(
                48.2081743,
                16.3638189,
                elevation=160,
                time=datetime(2023, 7, 3, 10, 0, 0, tzinfo=timezone.utc),
            ),
            GPXTrackPoint(
                48.2181743,
                16.4638189,
                elevation=160,
                time=datetime(2023, 7, 3, 11, 0, 0, tzinfo=timezone.utc),
            ),
        ]
    )
    track.segments.append(segment)
    gpx.tracks.append(track)

    gpx.waypoints.extend(
        [
            GPXWaypoint(48.2081743, 16.3638189, name="Start", symbol="Circle, Green"),
            GPXWaypoint(48.2091743, 16.4138189, name="Break", symbol="Restroom"),
            GPXWaypoint(48.2181743, 16.4638189, name="End", symbol="Circle, Blue"),
        ]
    )

    route = GPXRoute(
        name="Unit Test Route Name", description="Unit Test Route Description"
    )
    route.points.extend(
        [
            GPXRoutePoint(
                48.2081743,
                16.3738189,
                time=datetime(2023, 7, 3, 10, 0, 0, tzinfo=timezone.utc),
                name="Route Start",
                symbol="Circle, Green",
            ),
            GPXRoutePoint(
                48.2181743,
                16.4738189,
                time=datetime(2023, 7, 3, 11, 0, 0, tzinfo=timezone.utc),
                name="Route End",
                symbol="Circle, Blue",
            ),
        ]
    )
    gpx.routes.append(route)

    output = StringIO()

    return gpx, output


def test_print_header(gpx_data: Tuple[GPX, StringIO]) -> None:
    gpx, output = gpx_data
    calculator = GPXTableCalculator(gpx, output)
    calculator.print_header()
    assert (
        output.getvalue()
        == """## Unit Test GPX Name
* Unit Test Creator
* Total moving time: 01:00:00
* Total distance: 5 mi
* Default speed: 48.28 mph
"""
    )


def test_print_waypoints(gpx_data: Tuple[GPX, StringIO]) -> None:
    gpx, output = gpx_data
    calculator = GPXTableCalculator(gpx, output)
    calculator.print_waypoints()
    assert "## Track:" in output.getvalue()


def test_print_routes(gpx_data: Tuple[GPX, StringIO]) -> None:
    gpx, output = gpx_data
    calculator = GPXTableCalculator(gpx, output)
    calculator.print_routes()
    assert "## Route:" in output.getvalue()
    assert (
        """
## Route: Unit Test Route Name
* Unit Test Route Description

| Name                           |   Dist. | GL |  ETA  | Notes
| :----------------------------- | ------: | -- | ----: | :----
| Route Start                    |       0 |    |       | Circle, Green
| Route End                      |     0/0 |    |       | Circle, Blue
"""
        in output.getvalue()
    )


def test_get_points_data(gpx_data: Tuple[GPX, StringIO]) -> None:
    gpx, _ = gpx_data
    track_ext = GPXTrackExt(gpx.tracks[0])
    points_data = track_ext.get_points_data()
    assert len(points_data) == 2


def test_get_nearest_locations(gpx_data: Tuple[GPX, StringIO]) -> None:
    gpx, _ = gpx_data
    location = Location(48.2081744, 16.3638188)
    track_ext = GPXTrackExt(gpx.tracks[0])
    nearest_locations = track_ext.get_nearest_locations(location)
    assert len(nearest_locations) == 1


# ── Waypoint classifier ──────────────────────────────────────────────────────

def _make_waypoint_ext(name=None, symbol=None) -> GPXWaypointExt:
    return GPXWaypointExt(GPXWaypoint(latitude=0, longitude=0, name=name, symbol=symbol))


def test_classifier_symbol_gas_station() -> None:
    """'Gas Station' symbol triggers fuel stop with G marker."""
    wp = _make_waypoint_ext(name="Anywhere", symbol="Gas Station")
    assert wp.fuel_stop()
    assert wp.marker() == "G"
    assert wp.delay() == timedelta(minutes=15)


def test_classifier_name_regex_gas() -> None:
    """Name containing 'Gas' matches Gas Station classifier via regex."""
    wp = _make_waypoint_ext(name="Joe's Gas Stop")
    assert wp.fuel_stop()
    assert wp.marker() == "G"


def test_classifier_name_regex_restaurant() -> None:
    """Name containing 'Lunch' matches Restaurant classifier via regex."""
    wp = _make_waypoint_ext(name="Lunch at the Diner")
    assert not wp.fuel_stop()
    assert wp.marker() == "L"
    assert wp.delay() == timedelta(minutes=60)


def test_classifier_symbol_restroom() -> None:
    """'Restroom' symbol gives a 15-minute delay with no marker."""
    wp = _make_waypoint_ext(name="Break", symbol="Restroom")
    assert not wp.fuel_stop()
    assert wp.marker() == ""
    assert wp.delay() == timedelta(minutes=15)


def test_classifier_no_match() -> None:
    """Unrecognised symbol/name produces zero delay and no marker."""
    wp = _make_waypoint_ext(name="Random Point", symbol="Waypoint")
    assert not wp.fuel_stop()
    assert wp.marker() == ""
    assert wp.delay() == timedelta()


# ── shaping_point ─────────────────────────────────────────────────────────────

def test_shaping_point_no_name() -> None:
    wp = _make_waypoint_ext(name=None)
    assert wp.shaping_point()


def test_shaping_point_via_prefix() -> None:
    wp = _make_waypoint_ext(name="Via Seattle")
    assert wp.shaping_point()


def test_shaping_point_v_suffix() -> None:
    wp = _make_waypoint_ext(name="Turn here (V)")
    assert wp.shaping_point()


def test_shaping_point_regular() -> None:
    wp = _make_waypoint_ext(name="Normal Stop", symbol="Waypoint")
    assert not wp.shaping_point()


# ── Fuel stop resets last_gas in route ───────────────────────────────────────

def test_route_fuel_stop_distance_format() -> None:
    """Gas stop row shows 'since_gas/total'; non-fuel rows show only total."""
    gpx = GPX()
    route = GPXRoute(name="Fuel Test")
    route.points.extend([
        GPXRoutePoint(latitude=0.0, longitude=0.0, name="Start", symbol="Circle, Green"),
        GPXRoutePoint(latitude=0.0, longitude=1.0, name="Gas Stop", symbol="Gas Station"),
        GPXRoutePoint(latitude=0.0, longitude=2.0, name="End", symbol="Circle, Blue"),
    ])
    gpx.routes.append(route)
    output = StringIO()
    GPXTableCalculator(gpx, output, imperial=False).print_routes()
    lines = output.getvalue().splitlines()

    gas_line = next(line for line in lines if "Gas Stop" in line)
    start_line = next(line for line in lines if "Start" in line)
    end_line = next(line for line in lines if "End" in line)

    assert "/" in gas_line      # shows since_gas/total
    assert "/" not in start_line.split("|")[2]  # Start shows only "0"
    assert "/" in end_line       # last point always shows both distances


# ── Departure time propagates to ETA column ──────────────────────────────────

def test_route_departure_time_in_eta_column() -> None:
    """With depart_at set, the first waypoint's ETA reflects the departure time."""
    gpx = GPX()
    route = GPXRoute(name="Timing Test")
    route.points.extend([
        GPXRoutePoint(latitude=0.0, longitude=0.0, name="Start", symbol="Circle, Green"),
        GPXRoutePoint(latitude=0.0, longitude=1.0, name="End", symbol="Circle, Blue"),
    ])
    gpx.routes.append(route)
    output = StringIO()
    depart = datetime(2023, 7, 1, 9, 0, 0, tzinfo=timezone.utc)
    GPXTableCalculator(
        gpx, output, imperial=False, depart_at=depart, tz=timezone.utc
    ).print_routes()
    assert "09:00" in output.getvalue()


if __name__ == "__main__":
    pytest.main()
