import streamlit as st

from vector_page import render_vector_page


st.set_page_config(page_title="Data manipulation", page_icon="🛠️", layout="wide")
render_vector_page(enable_filters=True, cluster_points=False)
