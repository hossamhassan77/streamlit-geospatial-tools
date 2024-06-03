""" 

"""

import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster

st.set_page_config(page_title="data-visulization", layout="wide", page_icon="🗺️")
st.sidebar.markdown("# Vector data visulization 🛠️")

# upload file
uploaded_file = st.file_uploader(
    "Upload a file", type=["csv", "xlsx", "zip", "geojson"]
)
if uploaded_file:
    uploaded_file = uploaded_file.name
st.write("Or")
uploaded_file = st.text_input("Enter URL for vector dataset: ", "https://raw.githubusercontent.com/LonnyGomes/CountryGeoJSONCollection/master/geojson/EGY.geojson")
m = folium.Map(
    [0, 0],
    zoom_start=2
)
# Adding named basemaps
folium.TileLayer(
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    name="ESRI Satellite",
    attr="ESRI",
).add_to(m)
folium.TileLayer('CartoDB dark_matter', name='CartoDB Dark Matter').add_to(m)
marker_cluster = MarkerCluster().add_to(m)
if uploaded_file is not None:
    extension = uploaded_file.split(".")[-1]
    if extension in {"csv", "xlsx"}:
        if extension == "csv":
            data_frame = pd.read_csv(uploaded_file)
        else:
            data_frame = pd.read_excel(uploaded_file)
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            column_guess = data_frame.columns.str.contains("lat|latitude", case=False)
            index = 0
            if len(data_frame.columns[column_guess].tolist()) != 0:
                latitude_guess = data_frame.columns[column_guess].tolist()[0]
                index = data_frame.columns.get_loc(latitude_guess)
            lat = st.selectbox(
                "Choose latitude column:", data_frame.columns, index=index
            )
        with col2:
            column_guess = data_frame.columns.str.contains(
                "lng|long|longitude", case=False
            )
            index = 0
            if len(data_frame.columns[column_guess].tolist()) != 0:
                longitude_guess = data_frame.columns[column_guess].tolist()[0]
                index = data_frame.columns.get_loc(longitude_guess)
            lng = st.selectbox(
                "Choose longitude column:", data_frame.columns, index=index
            )
        data_frame = gpd.GeoDataFrame(
            data_frame,
            geometry=gpd.points_from_xy(data_frame[lng], data_frame[lat]),
            crs="wgs84",
        ).dropna(subset=[lng, lat])
        bounds = data_frame.total_bounds
        m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
        # Optionally, add markers for each point in the GeoDataFrame
        for _, row in data_frame.iterrows():
            folium.Marker(
                location=[row[lat], row[lng]],
            ).add_to(marker_cluster)
    else:
        data_frame = gpd.read_file(uploaded_file, crs="wgs84")
        bounds = data_frame.total_bounds
        m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
        folium.GeoJson(data_frame, name="Loaded data").add_to(m)
    st.dataframe(data_frame.drop(columns="geometry"))
folium.LayerControl().add_to(m)
st_folium(m, width=1000)
# input_name = st.text_input("Type you name:", key="name")
# data_frame = pd.read_csv(r"data/raptor_nest.csv").dropna(
#     subset=["lat_y_dd", "long_x_dd"]
# )
# options = ["Select column"]
# unique_values = ["Select value"]
# for column in data_frame.columns:
#     options.append(column)
# input_column = st.selectbox("Choose column:", options)
# if input_column != options[0]:
#     for value in data_frame[input_column].unique():
#         unique_values.append(value)
#     if data_frame[input_column].dtype == "O":
#         uvalue = st.selectbox("Select value:", unique_values, index=0)
#     else:
#         uvalue = st.slider(
#             "Select a range of values",
#             data_frame[input_column].min(),
#             data_frame[input_column].max(),
#             (data_frame[input_column].min(), data_frame[input_column].max()),
#         )
#     if uvalue != unique_values[0]:
#         data_frame = data_frame[data_frame[input_column] == uvalue]
