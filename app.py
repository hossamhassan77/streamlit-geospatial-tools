import streamlit as st

from app_components import StreamlitComponents


st.set_page_config(page_title="Geospatial Playground", page_icon="🌍", layout="wide")
StreamlitComponents().sidebar_info()

st.title("🚀 Python-Powered Geospatial Playground")
st.write(
    """
    An interactive workspace for loading, inspecting, filtering, analyzing, and visualizing
    spatial data. The project demonstrates practical Python GIS workflows in a browser-based
    Streamlit interface.
    """
)

text_column, image_column = st.columns((1, 3))
with text_column:
    st.subheader("Core technology")
    left, right = st.columns(2)
    with left:
        st.markdown(
            """
            - Streamlit
            - GeoPandas
            - Rasterio
            - PyProj
            - Pandas
            """
        )
    with right:
        st.markdown(
            """
            - Folium
            - Fiona
            - Shapely
            - SQLAlchemy
            - PostGIS (optional)
            """
        )



st.subheader("Available tools")
st.markdown(
    """
    1. **Vector visualization:** map CSV, Excel, GeoJSON, GeoPackage, KML, and zipped Shapefiles.
    2. **Data manipulation:** filter vector attributes and export the selected records.
    3. **Raster analysis:** inspect raster metadata, bands, statistics, and histograms.
    4. **Analytical tools:** calculate geometry measurements, buffers, and dissolved layers.
    """
)
