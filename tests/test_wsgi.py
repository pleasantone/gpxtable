import io

import pytest
import responses
from flask import url_for
from flask.testing import FlaskClient

from conftest import gpx_sample
from gpxtable.wsgi import InvalidSubmission, create_app, create_table

TEST_FILE_URL = "http://mock.api/basecamp.gpx"
TEST_FILE = gpx_sample("basecamp")
TEST_RESPONSE = b"Garmin Desktop App"
BAD_XML_FILE = gpx_sample("bad-xml")


def upload(path, filename: str = "test.gpx") -> tuple[io.BytesIO, str]:
    """Build a multipart upload tuple from a sample file, without leaking a handle."""
    return io.BytesIO(path.read_bytes()), filename


@pytest.fixture(scope="session")
def app():
    # add our fake responses
    responses.add(responses.GET, TEST_FILE_URL, status=200, body=TEST_FILE.read_bytes())
    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    return app


def test_index(client: FlaskClient) -> None:
    """Test the index page."""
    response = client.get(url_for("gpxtable.upload_file"))
    assert response.status_code == 200
    assert b"URL to GPX file" in response.data


def test_upload_file(client: FlaskClient) -> None:
    """Test file upload."""
    data = {"file": upload(TEST_FILE, "basecamp.gpx")}
    response = client.post(
        url_for("gpxtable.upload_file"), data=data, content_type="multipart/form-data"
    )
    assert response.status_code == 200
    assert TEST_RESPONSE in response.data


@responses.activate
def test_upload_url(client: FlaskClient) -> None:
    """Test URL submission."""

    response = client.post(
        url_for("gpxtable.upload_file"),
        data={"url": TEST_FILE_URL},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert TEST_RESPONSE in response.data


def test_bad_xml(client: FlaskClient) -> None:
    data = {"file": upload(BAD_XML_FILE, "bad-xml.gpx")}
    response = client.post(
        url_for("gpxtable.upload_file"),
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert response.history  # it was redirected
    assert response.history[0].location == "/"
    assert b"Unable to parse" in response.data


def test_about(client: FlaskClient) -> None:
    """Test the about page renders."""
    response = client.get(url_for("gpxtable.about"))
    assert response.status_code == 200
    assert b"documentation" in response.data


def test_missing_file_and_url(client: FlaskClient) -> None:
    """POST with neither file nor URL should redirect with error."""
    response = client.post(
        url_for("gpxtable.upload_file"), data={}, follow_redirects=True
    )
    assert response.history
    assert b"Missing URL" in response.data


def test_invalid_speed(client: FlaskClient) -> None:
    """Non-numeric speed value should redirect with error."""
    data = {"file": upload(TEST_FILE), "speed": "fast"}
    response = client.post(
        url_for("gpxtable.upload_file"),
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert response.history
    assert b"Invalid speed" in response.data


def test_invalid_timezone(client: FlaskClient) -> None:
    """Unknown timezone should redirect with error."""
    data = {"file": upload(TEST_FILE), "tz": "Fake/Zone"}
    response = client.post(
        url_for("gpxtable.upload_file"),
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert response.history
    assert b"Invalid timezone" in response.data


def test_invalid_departure(client: FlaskClient) -> None:
    """Unparseable departure time should redirect with error."""
    data = {"file": upload(TEST_FILE), "departure": "notadate"}
    response = client.post(
        url_for("gpxtable.upload_file"),
        data=data,
        content_type="multipart/form-data",
        follow_redirects=True,
    )
    assert response.history
    assert b"Invalid departure" in response.data


def test_invalid_url_scheme(client: FlaskClient) -> None:
    """Non-http/https URL scheme should redirect with error."""
    response = client.post(
        url_for("gpxtable.upload_file"),
        data={"url": "ftp://example.com/file.gpx"},
        follow_redirects=True,
    )
    assert response.history
    assert b"Invalid URL" in response.data


@responses.activate
def test_ssrf_loopback_blocked(client: FlaskClient) -> None:
    """Requests to loopback IPs should be blocked."""
    response = client.post(
        url_for("gpxtable.upload_file"),
        data={"url": "http://127.0.0.1/file.gpx"},
        follow_redirects=True,
    )
    assert response.history
    assert b"Invalid URL" in response.data


@responses.activate
def test_ssrf_private_ip_blocked(client: FlaskClient) -> None:
    """Requests to private-range IPs should be blocked."""
    response = client.post(
        url_for("gpxtable.upload_file"),
        data={"url": "http://192.168.1.1/file.gpx"},
        follow_redirects=True,
    )
    assert response.history
    assert b"Invalid URL" in response.data


@responses.activate
def test_url_fetch_failure(client: FlaskClient) -> None:
    """A URL that returns a non-200 status should redirect with error."""
    responses.add(responses.GET, "http://mock.api/fail.gpx", status=404)
    response = client.post(
        url_for("gpxtable.upload_file"),
        data={"url": "http://mock.api/fail.gpx"},
        follow_redirects=True,
    )
    assert response.history
    assert b"Unable to retrieve" in response.data


def test_create_table_markdown() -> None:
    """output_format='markdown' should return raw markdown, not HTML."""
    with open(TEST_FILE, "rb") as f:
        result = create_table(f, output_format="markdown")
    assert "##" in result
    assert "<table" not in result


def test_create_table_html() -> None:
    """output_format='html' (default) should return rendered HTML."""
    with open(TEST_FILE, "rb") as f:
        result = create_table(f, output_format="html")
    assert "<table" in result


def test_create_table_htmlcode() -> None:
    """output_format='htmlcode' should return HTML-escaped HTML."""
    with open(TEST_FILE, "rb") as f:
        result = create_table(f, output_format="htmlcode")
    assert "&lt;table" in result


def test_create_table_invalid_departure() -> None:
    """Unparseable departure string should raise InvalidSubmission."""
    with (
        open(TEST_FILE, "rb") as f,
        pytest.raises(InvalidSubmission, match="Invalid departure"),
    ):
        create_table(f, departure="notadate")


if __name__ == "__main__":
    pytest.main()
