"""Pure helpers shared by the Streamlit geospatial pages."""

from __future__ import annotations

import html
import ipaddress
import os
from pathlib import Path
from typing import Iterable
from urllib.parse import quote_plus, urlparse
import zipfile

import geopandas as gpd
import pandas as pd


LATITUDE_NAMES = ("latitude", "lat", "lat_y_dd", "y")
LONGITUDE_NAMES = ("longitude", "lon", "lng", "long", "long_x_dd", "x")


def source_extension(source_name: str) -> str:
    """Return a lowercase extension while ignoring URL query strings."""
    return Path(urlparse(source_name).path).suffix.lower().lstrip(".")


def validate_public_url(url: str) -> str:
    """Accept HTTP(S) URLs while rejecting credentials and obvious private hosts."""
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("Enter a valid HTTP or HTTPS URL.")
    if parsed.username or parsed.password:
        raise ValueError("URLs containing credentials are not allowed.")
    hostname = parsed.hostname.lower()
    if hostname == "localhost" or hostname.endswith(".local"):
        raise ValueError("Local network URLs are not allowed.")
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        return url
    if not address.is_global:
        raise ValueError("Private or local network URLs are not allowed.")
    return url


def guess_coordinate_column(columns: Iterable[object], candidates: tuple[str, ...]) -> str | None:
    """Find the best coordinate column using exact names before partial matches."""
    names = [str(column) for column in columns]
    normalized = {name.strip().lower(): name for name in names}
    for candidate in candidates:
        if candidate in normalized:
            return normalized[candidate]
    for name in names:
        lowered = name.strip().lower()
        if any(candidate in lowered for candidate in candidates):
            return name
    return None


def prepare_point_geodataframe(
    frame: pd.DataFrame, latitude_column: str, longitude_column: str
) -> gpd.GeoDataFrame:
    """Convert coordinate columns to a valid WGS84 point GeoDataFrame."""
    if latitude_column == longitude_column:
        raise ValueError("Latitude and longitude must use different columns.")

    result = frame.copy()
    result[latitude_column] = pd.to_numeric(result[latitude_column], errors="coerce")
    result[longitude_column] = pd.to_numeric(result[longitude_column], errors="coerce")
    result = result.dropna(subset=[latitude_column, longitude_column])
    result = result[
        result[latitude_column].between(-90, 90)
        & result[longitude_column].between(-180, 180)
    ]
    if result.empty:
        raise ValueError("No rows contain valid latitude and longitude values.")

    return gpd.GeoDataFrame(
        result,
        geometry=gpd.points_from_xy(result[longitude_column], result[latitude_column]),
        crs="EPSG:4326",
    )


def normalize_to_wgs84(frame: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Return a copy in WGS84, assigning WGS84 when a source has no CRS."""
    if frame.empty:
        return frame.copy()
    if frame.crs is None:
        return frame.set_crs("EPSG:4326", allow_override=True)
    return frame.to_crs("EPSG:4326")


def dataframe_for_export(frame: pd.DataFrame) -> pd.DataFrame:
    """Remove the active geometry column before tabular export."""
    if isinstance(frame, gpd.GeoDataFrame):
        return pd.DataFrame(frame.drop(columns=[frame.geometry.name]))
    return frame.copy()


def dataframe_to_csv(frame: pd.DataFrame) -> bytes:
    """Create an index-free UTF-8 CSV suitable for Streamlit downloads."""
    return dataframe_for_export(frame).to_csv(index=False).encode("utf-8")


def geodataframe_to_geojson(frame: gpd.GeoDataFrame) -> bytes:
    """Serialize a GeoDataFrame as UTF-8 GeoJSON."""
    return normalize_to_wgs84(frame).to_json().encode("utf-8")


def popup_html(properties: dict[object, object]) -> str:
    """Build escaped popup markup from feature attributes."""
    rows = [
        f"<b>{html.escape(str(key))}</b>: {html.escape(str(value))}<br>"
        for key, value in properties.items()
    ]
    return "<div style='max-height: 240px; overflow-y: auto;'>" + "".join(rows) + "</div>"


def valid_total_bounds(frame: gpd.GeoDataFrame) -> tuple[float, float, float, float] | None:
    """Return finite bounds or None for empty/invalid geometries."""
    if frame.empty or frame.geometry.is_empty.all():
        return None
    bounds = frame.total_bounds
    if len(bounds) != 4 or not all(pd.notna(value) for value in bounds):
        return None
    return tuple(float(value) for value in bounds)


def project_for_metric_operations(frame: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Project data to a suitable metric CRS for local distance operations."""
    if frame.crs is None:
        frame = frame.set_crs("EPSG:4326", allow_override=True)
    if frame.crs.is_projected:
        return frame.copy()
    estimated = frame.estimate_utm_crs()
    return frame.to_crs(estimated or "EPSG:3857")


def add_geometry_measurements(frame: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    """Add metric area and length columns without changing source geometry."""
    result = frame.copy()
    if result.crs is None:
        result = result.set_crs("EPSG:4326", allow_override=True)
    area_frame = result.to_crs("EPSG:6933")
    distance_frame = project_for_metric_operations(result)
    result["area_sq_km"] = area_frame.geometry.area / 1_000_000
    result["length_km"] = distance_frame.geometry.length / 1_000
    return result


def buffer_geometries(frame: gpd.GeoDataFrame, distance_meters: float) -> gpd.GeoDataFrame:
    """Buffer geometries in a local metric projection and restore the source CRS."""
    if distance_meters <= 0:
        raise ValueError("Buffer distance must be greater than zero.")
    source = frame if frame.crs is not None else frame.set_crs("EPSG:4326", allow_override=True)
    projected = project_for_metric_operations(source)
    buffered = projected.copy()
    buffered.geometry = projected.geometry.buffer(distance_meters)
    return buffered.to_crs(source.crs)


def safe_extract_zip(
    archive_path: str | Path,
    destination: str | Path,
    *,
    max_uncompressed_bytes: int = 500 * 1024 * 1024,
) -> Path:
    """Extract an archive after rejecting traversal and oversized payloads."""
    archive_path = Path(archive_path)
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(archive_path) as archive:
        members = archive.infolist()
        if len(members) > 10_000:
            raise ValueError("ZIP archive contains too many files.")
        if sum(item.file_size for item in members) > max_uncompressed_bytes:
            raise ValueError("ZIP archive is too large after extraction.")
        for item in members:
            unix_mode = item.external_attr >> 16
            if (unix_mode & 0o170000) == 0o120000:
                raise ValueError("ZIP archive contains a symbolic link.")
            target = (destination / item.filename).resolve()
            try:
                target.relative_to(destination)
            except ValueError as exc:
                raise ValueError("ZIP archive contains an unsafe path.") from exc
        archive.extractall(destination)

    entries = list(destination.iterdir())
    if len(entries) == 1 and entries[0].is_dir():
        return entries[0]
    return destination


def find_vector_file(folder: str | Path) -> Path:
    """Locate the first supported vector dataset in an extracted archive."""
    folder = Path(folder)
    for extension in (".shp", ".geojson", ".gpkg", ".kml"):
        matches = sorted(folder.rglob(f"*{extension}"))
        if matches:
            return matches[0]
    raise ValueError("The ZIP archive does not contain a supported vector dataset.")


def database_url_from_environment() -> str:
    """Build a PostgreSQL URL only when every required setting exists."""
    keys = ("DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME")
    values = {key: os.getenv(key) for key in keys}
    missing = [key for key, value in values.items() if not value]
    if missing:
        raise RuntimeError(f"Missing database settings: {', '.join(missing)}")
    return (
        f"postgresql+psycopg2://{quote_plus(values['DB_USER'])}:"
        f"{quote_plus(values['DB_PASSWORD'])}"
        f"@{values['DB_HOST']}:{values['DB_PORT']}/{values['DB_NAME']}"
    )
