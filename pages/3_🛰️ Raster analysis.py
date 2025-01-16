"""

"""

import json
import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import folium_static
from folium.plugins import MarkerCluster

class GeoDataManipulator:
    def __init__(self):
        self.map = folium.Map([0, 0], zoom_start=2)
        self.marker_cluster = MarkerCluster().add_to(self.map)
        self.uploaded_file = None
        self.data_frame = None
        self.latitude_column = None
        self.longitude_column = None
        self._setup_page()

    def _setup_page(self):
        st.set_page_config(
            page_title="data-visualization", layout="wide", page_icon="🗺️"
        )
        st.sidebar.markdown("# Vector data visualization 🗺️")
        self.uploaded_file = self._get_uploaded_file()
        self._add_basemaps()
        self._load_data()
st.sidebar.markdown("# Raster analysis 🛰️")
