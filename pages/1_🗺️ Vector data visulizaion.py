"""

"""
import os
import json
import streamlit as st
import pandas
import geopandas
import folium
import fiona
import random, string
import requests
from streamlit_folium import folium_static
from streamlit_folium import st_folium
from folium.plugins import MarkerCluster
from typing import Optional
from pyproj import CRS
from dotenv import load_dotenv
from pyproj.aoi import AreaOfInterest
from pyproj.database import query_utm_crs_info
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()
class GeoDataVisualizer:
    def __init__(self):
        self.map = folium.Map(location=[0, 0], zoom_start=2)
        self.base_map = "CartoDB positron"
        self._setup_page()
        self.workspace = self._generate_random_string()
        self.engine = create_engine(
            f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
        )
        self.postgis_connection = {
            "host": os.getenv("DB_HOST"),
            "port": os.getenv("DB_PORT"),
            "database": os.getenv("DB_NAME"),
            "schema": "public",
            "user": os.getenv("DB_USER"),
            "passwd": os.getenv("DB_PASSWORD"),
            "dbtype": "postgis",
        }
        self.uploaded_file = self._get_uploaded_file()
        if type(self.uploaded_file) == str:
            self.file_type = self.uploaded_file.split(".")[-1]
            self.store_name = f"{self.uploaded_file.split('.')[0].split('/')[-1]}_{self._generate_random_string()}"
        else:
            self.file_type = self.uploaded_file.name.split(".")[-1]
            self.store_name = f"{self.uploaded_file.name.split('.')[0]}_{self._generate_random_string()}"
        self._display_data()

    def _setup_page(self):
        """
        Setup the Streamlit page.

        This includes setting the page title, sidebar text, loading the data
        and adding a basemap to the map object.
        """
        st.set_page_config(
            page_title="data-visualization", layout="wide", page_icon="🗺️"
        )
        st.sidebar.markdown("# Vector data visualization 🗺️")
        self._add_basemaps()

    def _generate_random_string(self) -> str:
        """
        Generates a random 4-character string consisting of letters and digits.
        """
        return "".join(random.choices(string.ascii_letters + string.digits, k=4))

    def _get_uploaded_file(self):
        """Gets a file from the user. The file can be uploaded directly or selected from a list of options.

        The list of options is a list of URLs that point to GeoJSON files. The user can select one of these options
        instead of uploading a file. The selected file is then used as the input data for the application.

        Returns:
            The uploaded file or the selected URL.
        """
        file = st.file_uploader("Upload a file", type=["csv", "xlsx", "zip", "geojson", "kml", "tif", "geotiff", "img"])
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

    def save_vector_data_to_postgis(self, lat: Optional[str] = None, lng: Optional[str] = None) -> bool:
        """ """
        col1, _, col3, col4 = st.columns(4)
        if self.file_type in ("shp", "geojson"):
            geo_data_frame = geopandas.read_file(self.uploaded_file)
        elif self.file_type in ["csv", "xlsx"]:
            if self.file_type == "csv":
                data_frame = pandas.read_csv(self.uploaded_file)
            elif self.file_type == "xlsx":
                data_frame = pandas.read_excel(self.uploaded_file, engine="openpyxl")
            with col3:
                column_guess = data_frame.columns.str.contains(
                    "lat|latitude", case=False
                )
                lat_index = 0
                if len(data_frame.columns[column_guess].tolist()) != 0:
                    latitude_guess = data_frame.columns[column_guess].tolist()[0]
                    lat_index = data_frame.columns.get_loc(latitude_guess)
                latitude_column = st.selectbox(
                    "Choose latitude column:", data_frame.columns, index=lat_index
                )
            with col4:
                column_guess = data_frame.columns.str.contains(
                    "lng|long|longitude", case=False
                )
                lng_index = 0
                if len(data_frame.columns[column_guess].tolist()) != 0:
                    longitude_guess = data_frame.columns[column_guess].tolist()[0]
                    lng_index = data_frame.columns.get_loc(longitude_guess)
                longitude_column = st.selectbox(
                    "Choose longitude column:", data_frame.columns, index=lng_index
                )
            if longitude_column not in data_frame.columns or latitude_column not in data_frame.columns:
                print("Wrong latitude or longitude name.")
                return False
            if latitude_column is None or longitude_column is None:
                print("Latitude and longitude column names are required for csv and xlsx files.")
                return False
            geo_data_frame = geopandas.GeoDataFrame(
                data_frame,
                geometry=geopandas.points_from_xy(data_frame[longitude_column], data_frame[latitude_column]),
            ).dropna(subset=[longitude_column, latitude_column])
            utm_crs_list = query_utm_crs_info(
                datum_name="WGS 84",
                area_of_interest=AreaOfInterest(
                    west_lon_degree=data_frame[longitude_column].min(),
                    south_lat_degree=data_frame[latitude_column].min(),
                    east_lon_degree=data_frame[longitude_column].max(),
                    north_lat_degree=data_frame[latitude_column].max(),
                ),
            )
            if not utm_crs_list:
                raise ValueError("Unable to determine UTM CRS.")
            utm_crs = CRS.from_epsg(utm_crs_list[0].code)
            if geo_data_frame.crs is None:
                geo_data_frame = geo_data_frame.set_crs(utm_crs)
            geo_data_frame = geo_data_frame.to_crs(utm_crs)
        elif self.file_type == "kml":
            fiona.drvsupport.supported_drivers["LIBKML"] = "rw"
            with fiona.open(self.uploaded_file) as collection:
                geo_data_frame = geopandas.GeoDataFrame.from_features(collection)
        else:
            print(f"Unsupported file type: {self.file_type}")
            return False
        with col1:
                self.base_map = st.selectbox(
            "Choose basemap:",
            [
               "CartoDB positron" , "OpenStreetMap", "CartoDB dark_matter"])
                self._add_basemaps()
        # save to postgis
        if hasattr(geo_data_frame, "geometry") and geo_data_frame.geometry is not None:
            geo_data_frame.to_postgis(
                name=self.store_name,
                con=self.engine,
                if_exists="replace",
            )
            print("Data saved to PostGIS successfully.")
            return geo_data_frame
        print(f"{table_name} layer has no geometry column.")
        return False

    def create_workspace(self) -> bool or None:
        """Create a workspace in GeoServer."""
        url = f"{os.getenv('GEOSERVER_URL')}/rest/workspaces"
        headers = {"Content-Type": "application/json"}
        data = {"workspace": {"name": self.workspace}}
        response = requests.post(
            url,
            auth=(os.getenv("GEOSERVER_USERNAME"), os.getenv("GEOSERVER_PASSWORD")),
            json=data,
            headers=headers,
            timeout=15,
        )
        if response.status_code == 201:
            print(f"Workspace {self.workspace} created successfully.")
        elif response.status_code == 409:
            print("Workspace already exists.")
        else:
            print("Can't create workspace.")
            return False

    def create_datastore(self) -> bool or None:
        """Create a PostGIS data store in GeoServer."""
        url = f"{os.getenv('GEOSERVER_URL')}/rest/workspaces/{self.workspace}/datastores"
        headers = {"Content-Type": "application/json"}
        data = {
            "dataStore": {
                "name": self.store_name,
                "connectionParameters": self.postgis_connection,
            }
        }

        response = requests.post(
            url,
            auth=(os.getenv("GEOSERVER_USERNAME"), os.getenv("GEOSERVER_PASSWORD")),
            json=data,
            headers=headers,
            timeout=15,
        )
        if response.status_code == 201:
            print("Data store created successfully.")
        elif response.status_code == 409:
            print("Data store already exists.")
        else:
            print("Can't create data store.")
            return False

    def upload_data_to_geoserver(self, layer_name: str) -> None:
        """Publish a PostGIS table as a GeoServer vector layer."""
        url = f"{os.getenv('GEOSERVER_URL')}/rest/workspaces/{self.workspace}/datastores/{self.store_name}/featuretypes"
        headers = {"Content-Type": "application/json"}
        data = {"featureType": {"name": layer_name}}
        response = requests.post(
            url,
            auth=(os.getenv("GEOSERVER_USERNAME"), os.getenv("GEOSERVER_PASSWORD")),
            json=data,
            headers=headers,
            timeout=15,
        )
        if response.status_code == 201:
            print(f"Vector layer '{layer_name}' published successfully.")
        elif response.status_code == 409:
            print(f"Vector layer '{layer_name}' already exists.")
        else:
            print(f"cant publish vector layer: {response.text}.")

    def _add_basemaps(self):
        base_map_dict = {"OpenStreetMap": "OpenStreetMap", "CartoDB positron": "CartoDB positron", "CartoDB dark_matter": "CartoDB Dark"}
        # Add basemaps
        folium.TileLayer(self.base_map, name=base_map_dict[self.base_map], attr="a map").add_to(self.map)
    def _display_data(self):
        """ """
        self.save_vector_data_to_postgis()
        self.create_workspace()
        self.create_datastore()
        self.upload_data_to_geoserver(self.store_name)
        # WFS GeoJSON URL
        wfs_url = f"{os.getenv('GEOSERVER_URL')}/{self.workspace}/ows?service=WFS&version=1.0.0&request=GetFeature&typeName={self.workspace}:{self.store_name}&outputFormat=application/json"
        print(wfs_url)
        geo_feature_service = geopandas.read_file(wfs_url)
        col1, col2 = st.columns(2)
        with col1:
            bounds = geo_feature_service.total_bounds  
            # Add GeoDataFrame to the map
            for _, row in geo_feature_service.iterrows():
                popup_content = folium.Popup(str(row), max_width=300)  
                # Convert each geometry to GeoJSON and add it as a feature
                folium.GeoJson(
                    row.geometry,
                    name=row.get('name', 'Feature'),  # Replace 'name' with an appropriate column if available
                    popup=popup_content
                ).add_to(self.map)
            self.map.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
            st_folium(self.map, width=800, height=400)
        with col2:
            st.dataframe(geo_feature_service.drop(columns=["geometry", "id"]))

if __name__ == "__main__":
    GeoDataVisualizer()
