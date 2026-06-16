import geopandas as gpd
import streamlit as st
from streamlit_folium import st_folium

from geospatial_utils import (
    add_geometry_measurements,
    dataframe_for_export,
    buffer_geometries,
    geodataframe_to_geojson,
    normalize_to_wgs84,
)
from vector_page import build_map, load_vector_source


st.set_page_config(page_title="Analytical tools", page_icon="🔬", layout="wide")
st.title("Analytical tools")
st.caption("Measure geometries, create metric buffers, or dissolve features by an attribute.")

try:
    loaded = load_vector_source("analysis")
    if loaded is None:
        st.info("Choose a dataset to begin.")
        st.stop()
    source_frame, layer_name = loaded
    source_frame = source_frame[
        source_frame.geometry.notna() & ~source_frame.geometry.is_empty
    ].copy()
    if source_frame.empty:
        raise ValueError("The dataset has no valid geometries.")

    operation = st.selectbox(
        "Operation",
        ("Geometry measurements", "Buffer", "Dissolve"),
    )

    if operation == "Geometry measurements":
        result = add_geometry_measurements(source_frame)
        output_name = f"{layer_name}_measurements"
        st.info("Area uses a global equal-area CRS; length uses a locally estimated metric CRS.")
    elif operation == "Buffer":
        distance = st.number_input(
            "Buffer distance (meters)",
            min_value=1.0,
            value=1_000.0,
            step=100.0,
        )
        result = buffer_geometries(source_frame, distance)
        output_name = f"{layer_name}_buffer"
    else:
        columns = [
            column
            for column in source_frame.columns
            if column != source_frame.geometry.name
        ]
        if not columns:
            raise ValueError("Dissolve requires at least one attribute column.")
        dissolve_column = st.selectbox("Dissolve field", columns)
        result = source_frame.dissolve(by=dissolve_column, as_index=False)
        output_name = f"{layer_name}_dissolved"

    result = gpd.GeoDataFrame(result, geometry=result.geometry.name, crs=result.crs)
    map_frame = normalize_to_wgs84(result)

    metrics = st.columns(3)
    metrics[0].metric("Input features", f"{len(source_frame):,}")
    metrics[1].metric("Output features", f"{len(result):,}")
    metrics[2].metric("Geometry types", ", ".join(sorted(result.geometry.geom_type.unique())))

    map_column, table_column = st.columns((3, 2))
    with map_column:
        st.subheader("Result map")
        st_folium(
            build_map(map_frame, output_name, cluster_points=False),
            width=800,
            height=560,
            returned_objects=[],
        )
    with table_column:
        st.subheader("Result attributes")
        st.dataframe(
            dataframe_for_export(result),
            width="stretch",
            height=470,
        )
        st.download_button(
            "Download GeoJSON",
            geodataframe_to_geojson(result),
            file_name=f"{output_name}.geojson",
            mime="application/geo+json",
            width="stretch",
        )
except Exception as exc:
    st.error(f"Analysis failed: {exc}")
