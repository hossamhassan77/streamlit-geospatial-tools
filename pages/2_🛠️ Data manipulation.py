"""

"""

import streamlit as st

st.markdown("# Data manipulation in under constructions...🏗️")
st.sidebar.markdown("# Data manipulation 🛰️")


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
