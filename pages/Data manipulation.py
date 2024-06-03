""" 

"""

import streamlit as st
import pandas as pd
import geopandas as gpd

# upload file
uploaded_file = st.file_uploader(
    "Upload a file", type=["csv", "xlsx", "zip", "geojson"]
)
if uploaded_file is not None:
    extension = uploaded_file.name.split('.')[1]
    if extension in {"csv", "xlsx"}:
        if extension == "csv":
            data_frame = pd.read_csv(uploaded_file)
        else:
            data_frame = pd.read_excel(uploaded_file)
        col1, col2 = st.columns(2)
        with col1:
            column_guess = data_frame.columns.str.contains('lat', case=False)
            latitude_guess = data_frame.columns[column_guess].tolist()[0]
            lat = st.selectbox("Choose latitude column:", data_frame.columns, index=data_frame.columns.get_loc(latitude_guess))
        with col2:
            column_guess = data_frame.columns.str.contains('lng|long', case=False)
            longitude_guess = data_frame.columns[column_guess].tolist()[0]
            print(f'***************************{longitude_guess}')
            lng = st.selectbox("Choose longitude column:", data_frame.columns, index=data_frame.columns.get_loc(longitude_guess))
        data_frame = gpd.GeoDataFrame(
            data_frame,
            geometry=gpd.points_from_xy(data_frame[lng], data_frame[lat]),
        ).dropna(subset=[lng, lat])
    else:
        data_frame = gpd.read_file(uploaded_file)

    st.write(data_frame)
    st.map(data_frame, latitude=lat, longitude=lng)
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
