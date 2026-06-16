"""Reusable Streamlit vector-data explorer."""

from __future__ import annotations

import html
from pathlib import Path
import tempfile

from branca.element import Element
import folium
from folium.plugins import MarkerCluster
import geopandas as gpd
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from geospatial_utils import (
    LATITUDE_NAMES,
    LONGITUDE_NAMES,
    dataframe_for_export,
    dataframe_to_csv,
    find_vector_file,
    guess_coordinate_column,
    normalize_to_wgs84,
    popup_html,
    prepare_point_geodataframe,
    safe_extract_zip,
    source_extension,
    validate_public_url,
    valid_total_bounds,
)


SAMPLES = {
    "Neighborhood names (points)": Path("data/Neighborhood Names GIS.geojson"),
    "Vienna streets (lines)": Path("data/vienna-streets.geojson"),
    "World boundaries (polygons)": Path("data/world-boundaries.geojson"),
    "Countries (CSV points)": Path("data/countries.csv"),
    "Egyptian cities (CSV points)": Path("data/eg.csv"),
}
MAX_POINT_MARKERS = 5_000


def _read_tabular(source, extension: str) -> pd.DataFrame:
    if extension == "csv":
        return pd.read_csv(source)
    if extension == "xlsx":
        return pd.read_excel(source, engine="openpyxl")
    raise ValueError(f"Unsupported table format: {extension}")


def _read_uploaded_vector(uploaded_file) -> gpd.GeoDataFrame:
    extension = source_extension(uploaded_file.name)
    with tempfile.TemporaryDirectory(prefix="geo_upload_") as temp_dir:
        path = Path(temp_dir) / Path(uploaded_file.name).name
        path.write_bytes(uploaded_file.getvalue())
        if extension == "zip":
            extracted = safe_extract_zip(path, Path(temp_dir) / "extracted")
            path = find_vector_file(extracted)
        return gpd.read_file(path)


def _select_coordinates(frame: pd.DataFrame, key_prefix: str) -> tuple[str, str]:
    columns = list(frame.columns)
    if not columns:
        raise ValueError("The table has no columns.")
    latitude_guess = guess_coordinate_column(columns, LATITUDE_NAMES)
    longitude_guess = guess_coordinate_column(columns, LONGITUDE_NAMES)
    col1, col2 = st.columns(2)
    with col1:
        latitude = st.selectbox(
            "Latitude column",
            columns,
            index=columns.index(latitude_guess) if latitude_guess else 0,
            key=f"{key_prefix}_latitude",
        )
    with col2:
        longitude = st.selectbox(
            "Longitude column",
            columns,
            index=columns.index(longitude_guess) if longitude_guess else min(1, len(columns) - 1),
            key=f"{key_prefix}_longitude",
        )
    return str(latitude), str(longitude)


def load_vector_source(key_prefix: str) -> tuple[gpd.GeoDataFrame, str] | None:
    """Render source controls and return a normalized vector dataset."""
    mode = st.radio(
        "Data source",
        ("Sample Data", "Upload file", "Public URL"),
        horizontal=True,
        key=f"{key_prefix}_source_mode",
    )

    if mode == "Sample Data":
        label = st.selectbox("Sample dataset", list(SAMPLES), key=f"{key_prefix}_sample")
        source = SAMPLES[label]
        name = source.stem
        extension = source_extension(str(source))
    elif mode == "Upload file":
        uploaded = st.file_uploader(
            "Upload CSV, XLSX, GeoJSON, GeoPackage, KML, or zipped Shapefile",
            type=["csv", "xlsx", "geojson", "json", "gpkg", "kml", "zip"],
            key=f"{key_prefix}_upload",
        )
        if uploaded is None:
            return None
        name = Path(uploaded.name).stem
        extension = source_extension(uploaded.name)
        if extension in {"csv", "xlsx"}:
            table = _read_tabular(uploaded, extension)
            latitude, longitude = _select_coordinates(table, key_prefix)
            return prepare_point_geodataframe(table, latitude, longitude), name
        return normalize_to_wgs84(_read_uploaded_vector(uploaded)), name
    else:
        source = st.text_input(
            "Public data URL",
            placeholder="https://example.com/data.geojson",
            key=f"{key_prefix}_url",
        ).strip()
        if not source:
            return None
        source = validate_public_url(source)
        name = Path(source.split("?")[0]).stem or "remote_data"
        extension = source_extension(source)

    if extension in {"csv", "xlsx"}:
        table = _read_tabular(source, extension)
        latitude, longitude = _select_coordinates(table, key_prefix)
        return prepare_point_geodataframe(table, latitude, longitude), name
    if extension not in {"geojson", "json", "gpkg", "kml"}:
        raise ValueError(f"Unsupported data format: .{extension or 'unknown'}")
    return normalize_to_wgs84(gpd.read_file(source)), name


def _filter_column(
    source_frame: gpd.GeoDataFrame,
    current_frame: gpd.GeoDataFrame,
    column: str,
    key_prefix: str,
) -> gpd.GeoDataFrame:
    """Render one column filter and apply it with AND logic."""
    series = source_frame[column]
    key_base = f"{key_prefix}_filter_{column}"

    with st.sidebar.expander(str(column), expanded=True):
        if pd.api.types.is_bool_dtype(series.dtype):
            values = st.multiselect(
                "Values",
                [True, False],
                default=[True, False],
                key=f"{key_base}_bool",
            )
            return current_frame[current_frame[column].isin(values)]

        if pd.api.types.is_numeric_dtype(series.dtype):
            valid = series.dropna()
            if valid.empty:
                st.info("No numeric values.")
                return current_frame
            minimum, maximum = float(valid.min()), float(valid.max())
            if minimum == maximum:
                st.info(f"All values are {minimum:g}.")
                return current_frame
            selected_range = st.slider(
                "Range",
                minimum,
                maximum,
                (minimum, maximum),
                key=f"{key_base}_numeric",
            )
            return current_frame[current_frame[column].between(*selected_range)]

        if pd.api.types.is_datetime64_any_dtype(series.dtype):
            valid = series.dropna()
            if valid.empty:
                st.info("No date values.")
                return current_frame
            selected_range = st.date_input(
                "Date range",
                value=(valid.min().date(), valid.max().date()),
                key=f"{key_base}_date",
            )
            if len(selected_range) != 2:
                return current_frame
            dates = pd.to_datetime(current_frame[column]).dt.date
            return current_frame[dates.between(selected_range[0], selected_range[1])]

        options = sorted(series.dropna().astype(str).unique().tolist())
        if not options:
            st.info("No values.")
            return current_frame
        selected_values = st.multiselect(
            "Values",
            options,
            default=options,
            key=f"{key_base}_category",
        )
        return current_frame[current_frame[column].astype(str).isin(selected_values)]


def filter_frame(frame: gpd.GeoDataFrame, key_prefix: str) -> gpd.GeoDataFrame:
    """Render multiple column filters and combine them with AND logic."""
    st.sidebar.subheader("Data filter")
    columns = [column for column in frame.columns if column != frame.geometry.name]
    selected_columns = st.sidebar.multiselect(
        "Filter columns (AND)",
        columns,
        key=f"{key_prefix}_filter_columns",
    )
    if not selected_columns:
        return frame

    filtered = frame.copy()
    for column in selected_columns:
        filtered = _filter_column(frame, filtered, str(column), key_prefix)
    return filtered


def _add_basemaps(map_object: folium.Map) -> None:
    folium.TileLayer(
        tiles=(
            "https://server.arcgisonline.com/ArcGIS/rest/services/"
            "World_Imagery/MapServer/tile/{z}/{y}/{x}"
        ),
        name="ESRI Satellite",
        attr="Esri",
    ).add_to(map_object)
    folium.TileLayer("CartoDB dark_matter", name="CartoDB Dark").add_to(map_object)


def _legend_symbol(geometry_types: set[str]) -> str:
    if geometry_types and geometry_types <= {"Point"}:
        return (
            "<span style='display:inline-block;width:10px;height:10px;"
            "border-radius:50%;background:#1769aa;border:1px solid #1769aa;'></span>"
        )
    if geometry_types and geometry_types <= {"LineString", "MultiLineString"}:
        return (
            "<span style='display:inline-block;width:18px;height:0;"
            "border-top:3px solid #1769aa;vertical-align:middle;'></span>"
        )
    return (
        "<span style='display:inline-block;width:14px;height:10px;"
        "background:#1769aa55;border:1px solid #1769aa;'></span>"
    )


def build_map(
    frame: gpd.GeoDataFrame,
    layer_name: str,
    cluster_points: bool,
) -> folium.Map:
    """Build a Folium map for point, line, polygon, or mixed vector data."""
    map_object = folium.Map(location=[0, 0], zoom_start=2, control_scale=True)
    _add_basemaps(map_object)
    bounds = valid_total_bounds(frame)
    if bounds:
        min_x, min_y, max_x, max_y = bounds
        map_object.fit_bounds([[min_y, min_x], [max_y, max_x]])

    geometry_types = set(frame.geometry.geom_type.dropna())
    if geometry_types and geometry_types <= {"Point"}:
        target = MarkerCluster(name=layer_name).add_to(map_object) if cluster_points else map_object
        attributes = dataframe_for_export(frame)
        for position, (_, row) in enumerate(frame.iterrows()):
            if position >= MAX_POINT_MARKERS:
                break
            geometry = row.geometry
            if geometry is None or geometry.is_empty:
                continue
            properties = attributes.iloc[position].to_dict()
            folium.CircleMarker(
                location=[geometry.y, geometry.x],
                radius=5,
                popup=folium.Popup(popup_html(properties), max_width=350),
                color="#1769aa",
                fill=True,
                fill_opacity=0.75,
            ).add_to(target)
    else:
        fields = list(dataframe_for_export(frame).columns)
        popup = folium.GeoJsonPopup(fields=fields, aliases=fields, localize=True) if fields else None
        folium.GeoJson(
            frame.__geo_interface__,
            name=layer_name,
            zoom_on_click=True,
            highlight_function=lambda _: {"weight": 4, "fillOpacity": 0.65},
            popup=popup,
        ).add_to(map_object)

    folium.LayerControl(collapsed=False).add_to(map_object)
    
    return map_object


def render_vector_page(
    *,
    enable_filters: bool,
    cluster_points: bool,
) -> None:
    """Render a complete vector explorer page."""
    key_prefix = "manipulation" if enable_filters else "visualization"
    st.title("Data manipulation" if enable_filters else "Vector data visualization")
    st.caption(
        "Load tabular coordinates or vector files, inspect attributes, and export the result."
    )

    try:
        loaded = load_vector_source(key_prefix)
        if loaded is None:
            st.info("Choose a Sample Data, upload a file, or enter a public URL.")
            return
        frame, layer_name = loaded
        frame = frame[frame.geometry.notna() & ~frame.geometry.is_empty].copy()
        if enable_filters:
            frame = filter_frame(frame, key_prefix)
        if frame.empty:
            st.warning("No features match the current input and filters.")
            return
    except Exception as exc:
        st.error(f"Could not load the dataset: {exc}")
        return

    if len(frame) > MAX_POINT_MARKERS and set(frame.geometry.geom_type) <= {"Point"}:
        st.warning(f"The map displays the first {MAX_POINT_MARKERS:,} points for performance.")

    metrics = st.columns(3)
    metrics[0].metric("Features", f"{len(frame):,}")
    metrics[1].metric("Columns", len(dataframe_for_export(frame).columns))
    metrics[2].metric("CRS", str(frame.crs or "Unknown"))

    map_column, data_column = st.columns((3, 2))
    with map_column:
        st.subheader("Map")
        st_folium(
            build_map(frame, layer_name, cluster_points),
            width=800,
            height=560,
            returned_objects=[],
        )
    with data_column:
        st.subheader("Attributes")
        table = dataframe_for_export(frame)
        st.dataframe(table, width="stretch", height=470)
        st.download_button(
            "Download filtered CSV" if enable_filters else "Download CSV",
            dataframe_to_csv(frame),
            file_name=f"{layer_name}.csv",
            mime="text/csv",
            width="stretch",
        )
