"""Shared application components and optional service configuration."""

from pathlib import Path

from dotenv import load_dotenv
import streamlit as st

from geospatial_utils import database_url_from_environment, safe_extract_zip

load_dotenv()


class StreamlitComponents:
    """Reusable Streamlit interface elements."""

    def sidebar_info(self) -> None:
        st.sidebar.markdown("# Project Repository")
        st.sidebar.info(
            "[Geospatial Playground](https://github.com/hossamhassan77/streamlit-geospatial-tools)"
        )
        st.sidebar.markdown("# Contact")
        st.sidebar.info(
            """
            - LinkedIn: [Hossam Nasr](https://www.linkedin.com/in/hossamnasr7)
            - Resume: [GIS Developer](https://docs.google.com/document/d/1ErNBGm1goZTcLyuKwYAi-q3RCIRU9qx49oy_m4xmQh0/edit?usp=sharing)
            """
        )


class GeospatialTools:
    """Optional helpers for database and archive-backed workflows."""

    def __init__(self, folder_path: str = None) -> None:
        self.folder_path = Path(folder_path) if folder_path else None
        self.engine = None

    def create_database_engine(self):
        """Create a SQLAlchemy engine only when database access is requested."""
        from sqlalchemy import create_engine

        if self.engine is None:
            self.engine = create_engine(database_url_from_environment(), pool_pre_ping=True)
        return self.engine

    @staticmethod
    def get_file_type(file_path: str) -> str:
        file = Path(file_path)
        if file.suffix.lower() == ".zip":
            return "gdb" if file.stem.lower().endswith(".gdb") else "shp"
        return file.suffix.lower().lstrip(".")

    @staticmethod
    def decompress_zip(folder_path: str, destination: str = "storage") -> str:
        return str(safe_extract_zip(folder_path, destination))

    @staticmethod
    def upload_vector_data():
        """Render a reusable vector upload widget."""
        uploaded = st.file_uploader(
            "Upload a vector file",
            type=["csv", "xlsx", "zip", "geojson", "gpkg", "kml"],
        )
        if uploaded:
            return uploaded
        return st.text_input("Or enter a public data URL")
