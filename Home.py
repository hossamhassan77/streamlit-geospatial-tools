import streamlit as st
from app_components import StreamlitComponents
components = StreamlitComponents()

st.set_page_config(
    page_title="Geospatial Playground",
    page_icon="🌍",
    layout="wide",
)
components.sidebar_info()

st.markdown("## Python-Powered Geospatial Playground!")
st.write(
    """
    A web-based platform for geospatial analysis and visualization, built entirely with Python!
    This isn't a commercial venture, but rather a showcase of the skills I've been honing.
    It's a playground where I can explore various geospatial functionalities and experiment with
    different analysis and visualization techniques.
    Think of it as a dynamic portfolio, demonstrating the capabilities of Python in the realm of
    geospatial data.
    """
)
col1, col2 = st.columns((1, 3))
with col1:
    st.write(
    """
    ### Used technology:
    """
    )
    col1_1, col1_2 = st.columns((1, 2))
    with col1_1:
        st.write(
        """
        - Streamlit.
        - GeoServer.
        - PostGIS.
        - GDAL.
        - Pyproj.
        - Pandas.
        """
    )
    with col1_2:
        st.write(
        """
        - Geoalchemy.
        - Geopandas.
        - Sqlalchemy.
        - Folium.
        - Fiona.
        - Gemini.
        """
    )
with col2:
    st.image(r"imgs\Gemini_Generated_Image_j5jdi2j5jdi2j5jd.png", use_container_width=True)
