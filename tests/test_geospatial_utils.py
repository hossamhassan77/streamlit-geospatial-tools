import os
from pathlib import Path
import tempfile
import unittest
import zipfile

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

from geospatial_utils import (
    LATITUDE_NAMES,
    LONGITUDE_NAMES,
    add_geometry_measurements,
    buffer_geometries,
    dataframe_to_csv,
    database_url_from_environment,
    guess_coordinate_column,
    popup_html,
    prepare_point_geodataframe,
    safe_extract_zip,
    source_extension,
    validate_public_url,
)


class GeospatialUtilsTests(unittest.TestCase):
    def test_source_extension_ignores_url_query(self):
        self.assertEqual(source_extension("https://example.test/data.GEOJSON?download=1"), "geojson")

    def test_public_url_validation_rejects_local_addresses(self):
        self.assertEqual(
            validate_public_url("https://example.test/data.geojson"),
            "https://example.test/data.geojson",
        )
        with self.assertRaises(ValueError):
            validate_public_url("http://127.0.0.1/private.geojson")

    def test_coordinate_guess_prefers_exact_names(self):
        columns = ["estimated_latitude", "latitude", "longitude"]
        self.assertEqual(guess_coordinate_column(columns, LATITUDE_NAMES), "latitude")
        self.assertEqual(guess_coordinate_column(columns, LONGITUDE_NAMES), "longitude")

    def test_point_conversion_drops_invalid_coordinates(self):
        frame = pd.DataFrame(
            {
                "lat": ["30", "bad", 95],
                "lon": ["31", "32", 33],
                "name": ["valid", "text", "range"],
            }
        )
        result = prepare_point_geodataframe(frame, "lat", "lon")
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0]["name"], "valid")
        self.assertEqual(result.crs.to_string(), "EPSG:4326")

    def test_point_conversion_rejects_same_column(self):
        with self.assertRaises(ValueError):
            prepare_point_geodataframe(pd.DataFrame({"x": [1]}), "x", "x")

    def test_csv_export_excludes_geometry_and_index(self):
        frame = gpd.GeoDataFrame(
            {"name": ["Cairo"]},
            geometry=[Point(31.2, 30.0)],
            crs="EPSG:4326",
        )
        exported = dataframe_to_csv(frame).decode("utf-8")
        self.assertEqual(exported, "name\r\nCairo\r\n")

    def test_popup_html_escapes_untrusted_values(self):
        rendered = popup_html({"<key>": "<script>alert(1)</script>"})
        self.assertNotIn("<script>", rendered)
        self.assertIn("&lt;script&gt;", rendered)

    def test_safe_zip_extraction_rejects_traversal(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            archive = Path(temp_dir) / "unsafe.zip"
            with zipfile.ZipFile(archive, "w") as handle:
                handle.writestr("../outside.txt", "unsafe")
            with self.assertRaises(ValueError):
                safe_extract_zip(archive, Path(temp_dir) / "output")

    def test_measurement_and_buffer_operations(self):
        frame = gpd.GeoDataFrame(
            {"name": ["point"]},
            geometry=[Point(31.2, 30.0)],
            crs="EPSG:4326",
        )
        measured = add_geometry_measurements(frame)
        self.assertIn("area_sq_km", measured.columns)
        self.assertIn("length_km", measured.columns)
        buffered = buffer_geometries(frame, 100)
        self.assertEqual(buffered.crs, frame.crs)
        self.assertGreater(buffered.geometry.iloc[0].area, 0)

    def test_database_configuration_is_validated_lazily(self):
        keys = ("DB_USER", "DB_PASSWORD", "DB_HOST", "DB_PORT", "DB_NAME")
        original = {key: os.environ.pop(key, None) for key in keys}
        try:
            with self.assertRaises(RuntimeError):
                database_url_from_environment()
        finally:
            for key, value in original.items():
                if value is not None:
                    os.environ[key] = value


if __name__ == "__main__":
    unittest.main()
