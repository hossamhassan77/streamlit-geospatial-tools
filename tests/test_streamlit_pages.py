from pathlib import Path
import unittest

import geopandas as gpd
from shapely.geometry import Point
from streamlit.testing.v1 import AppTest

from vector_page import build_map


class StreamlitPageSmokeTests(unittest.TestCase):
    def test_all_pages_render_without_exceptions(self):
        pages = [Path("Home.py"), *sorted(Path("pages").glob("*.py"))]
        for page in pages:
            with self.subTest(page=page.name):
                app = AppTest.from_file(str(page), default_timeout=90).run()
                messages = [exception.message for exception in app.exception]
                self.assertEqual(messages, [])

    def test_data_manipulation_map_can_render_without_cluster_and_with_legend(self):
        frame = gpd.GeoDataFrame(
            {"name": ["A", "B"]},
            geometry=[Point(31.2, 30.0), Point(31.3, 30.1)],
            crs="EPSG:4326",
        )
        rendered = build_map(
            frame,
            "test layer",
            cluster_points=False,
            show_legend=True,
        ).get_root().render()
        self.assertIn("Legend", rendered)
        self.assertIn("test layer", rendered)
        self.assertNotIn("marker_cluster", rendered)


if __name__ == "__main__":
    unittest.main()
