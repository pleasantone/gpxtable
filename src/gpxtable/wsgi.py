"""
gpxtable.wsgi - Flask Blueprint/Application for running gpxtable as a server
"""

from __future__ import annotations

import html
import io
import os
import secrets
from datetime import datetime, tzinfo
from typing import IO
from urllib.parse import urlparse

import dateutil.parser
import dateutil.tz
import gpxpy.gpx
import markdown2
import requests
from flask import (
    Blueprint,
    Flask,
    Response,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)

from gpxtable import GPXTableCalculator


class InvalidSubmission(Exception):
    """Exception for invalid form submission"""


bp = Blueprint("gpxtable", __name__)


@bp.errorhandler(InvalidSubmission)
def invalid_submission(err: InvalidSubmission) -> Response:
    """Handles invalid form submissions and redirects to the upload file page."""
    flash(str(err))
    current_app.logger.info(err)
    return redirect(url_for("gpxtable.upload_file"))


def create_table(
    stream: IO[bytes],
    *,
    tz: tzinfo | None = None,
    departure: str | None = None,
    ignore_times: bool = False,
    display_coordinates: bool = False,
    imperial: bool = True,
    speed: float = 0.0,
    output_format: str = "html",
) -> str:
    """
    Creates a table from a GPX stream.

    Args:
        stream: The GPX stream data.
        tz: The timezone information (default: local time).
        departure: Departure time string (default: None).
        ignore_times: Ignore track times (default: False).
        display_coordinates: Display lat/lon (default: False).
        imperial: Use imperial units (default: True).
        speed: Travel speed override (default: 0.0).
        output_format: Output format — 'markdown', 'html', or 'htmlcode'.

    Returns:
        str: The formatted table output.
    """
    if tz is None:
        tz = dateutil.tz.tzlocal()
    depart_at = (
        dateutil.parser.parse(
            departure,
            default=datetime.now(tz).replace(minute=0, second=0, microsecond=0),
        )
        if departure
        else None
    )

    with io.StringIO() as buffer:
        try:
            GPXTableCalculator(
                gpxpy.parse(stream),
                output=buffer,
                depart_at=depart_at,
                ignore_times=ignore_times,
                display_coordinates=display_coordinates,
                imperial=imperial,
                speed=speed,
                tz=tz,
            ).print_all()
        except gpxpy.gpx.GPXXMLSyntaxException as err:
            raise InvalidSubmission(f"Unable to parse GPX information: {err}") from err

        output = buffer.getvalue()

    if output_format == "markdown":
        return output
    rendered = str(
        markdown2.markdown(
            output,
            extras={"tables": None, "html-classes": {"table": "gpxtable"}},
        )
    )
    return html.escape(rendered) if output_format == "htmlcode" else rendered


@bp.route("/", methods=["GET", "POST"])
def upload_file() -> str:
    """Handles file upload and URL submission, otherwise renders the upload page."""
    if request.method != "POST":
        return render_template("upload.html")

    if url := request.form.get("url"):
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise InvalidSubmission("Invalid URL")
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            file: IO[bytes] = io.BytesIO(response.content)
        except requests.RequestException as err:
            raise InvalidSubmission(f"Unable to retrieve URL: {err}") from err
    elif file := request.files.get("file"):
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if not file.filename:
            raise InvalidSubmission("No file selected")
    else:
        raise InvalidSubmission("Missing URL for GPX file or uploaded file.")

    tz = None
    if timezone := request.form.get("tz"):
        tz = dateutil.tz.gettz(timezone)
        if not tz:
            raise InvalidSubmission("Invalid timezone")

    result = create_table(
        file,
        tz=tz,
        departure=request.form.get("departure"),
        ignore_times=request.form.get("ignore_times") == "on",
        display_coordinates=request.form.get("coordinates") == "on",
        imperial=request.form.get("metric") != "on",
        speed=float(request.form.get("speed") or 0.0),
        output_format=request.form.get("output") or "html",
    )
    return render_template("results.html", output=result, format=request.form.get("output"))


@bp.route("/about")
def about() -> str:
    """Renders the about page."""
    return render_template("about.html")


def create_app() -> Flask:
    """Factory for creating the Flask application."""
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1000 * 1000  # 16mb
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or secrets.token_urlsafe(32)
    app.register_blueprint(bp)
    return app
