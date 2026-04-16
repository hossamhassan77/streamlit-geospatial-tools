import os
import pandas
import geopandas
from sqlalchemy import create_engine
from dotenv import load_dotenv
import streamlit as st
from pathlib import Path
import zipfile
from typing import Optional

load_dotenv()
class StreamlitComponents:
    """
    This class is a placeholder for any custom Streamlit components that may be developed in the future.
    It can be used to encapsulate and organize any additional functionality or features that are not part
    of the main application logic.
    """
    def __init__(self):
        pass
    def sidebar_info(self):
        """
        Set up the main page with GitHub repository and contact information.

        This function adds a sidebar with two sections: the first section contains a link to the
        GitHub repository for this application, and the second section contains a link to the
        author's LinkedIn profile and a link to the author's resume as a GIS Developer.
        """
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
    """A class for handling geospatial data processing and visualization tasks."""
    def __init__(self, folder_path = None) -> None:
        """
        Initializes the GDBReader class with a specified geodatabase folder path.

        This constructor sets up a database engine for connecting to a PostgreSQL/PostGIS
        database using environment variables for credentials. It also decompresses the
        provided geodatabase ZIP file, establishes a connection configuration dictionary
        for PostGIS, and generates a random store name.

        Parameters:
        -----------
        gdb_folder_path : str
            The path to the ZIP file containing the File Geodatabase to be processed.
        """
        self.engine = create_engine(
            f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
        )
        if folder_path is None:
            pass
        else:
            self.file_type = self._get_file_extension(folder_path)
            if self.file_type == "gdb":
                self.gdb_folder_path = self._decompress_zip(folder_path)
            else:
                self.gdb_folder_path = folder_path
        self.postgis_connection = {
            "host": os.getenv("DB_HOST"),
            "port": os.getenv("DB_PORT"),
            "database": os.getenv("DB_NAME"),
            "schema": "public",
            "user": os.getenv("DB_USER"),
            "passwd": os.getenv("DB_PASSWORD"),
            "dbtype": "postgis",
        }
        # self.store_name = self._generate_random_string()
        self.geometry_type = None
    def _get_file_extension(self, file_path):
        """
        Detect the file extension and perform additional checks for .zip files.

        Args:
            file_path (str): The path to the file.

        Returns:
            str: Message about the file type or additional checks.
        """
        file = Path(file_path)
        extension = file.suffix  # Extract the file extension

        if extension == ".zip":
            # Check if the last 4 characters before .zip are .gdb
            if file.stem.endswith(".gdb"):
                return "gdb"
            return "shp"
        return extension.lstrip(".")
    
    def _decompress_zip(self, folder_path) -> str:
        """
        Decompresses a ZIP file containing a File Geodatabase.

        Args:
            None

        Returns:
            str: The path to the extracted folder.
        """
        if not folder_path.endswith(".zip"):
            return folder_path
        # Directory where the contents will be extracted
        extract_to_path = "./storage/"
        # Create the extraction directory if it doesn't exist
        os.makedirs(extract_to_path, exist_ok=True)
        # Open and extract the zip file
        with zipfile.ZipFile(folder_path, "r") as zip_ref:
            # Extract all contents
            zip_ref.extractall(extract_to_path)
        # To list files in the zip without extracting
        with zipfile.ZipFile(folder_path, "r") as zip_ref:
            return os.path.abspath(f"{extract_to_path}/{zip_ref.namelist()[0][:-1]}")

    def upload_vector_data(self):
        """Provides a Streamlit interface for uploading vector data files or entering a URL."""
        file = st.file_uploader("Upload a file", type=["csv", "xlsx", "zip", "geojson", "kml"])
        if file:
            return file
        st.write("Or")
        return st.selectbox(
            "Choose an option",
            [
                "https://raw.githubusercontent.com/incubated-geek-cc/xy-to-latlng-convertor/main/data/CHASClinics_Output.csv",
                "https://raw.githubusercontent.com/LonnyGomes/CountryGeoJSONCollection/master/geojson/EGY.geojson",
                "https://raw.githubusercontent.com/openlayers/openlayers/main/examples/data/geojson/vienna-streets.geojson",
            ],
        )