from contextlib import nullcontext
import os
from pathlib import Path
import tempfile

os.environ.setdefault(
    "MPLCONFIGDIR",
    str(Path(tempfile.gettempdir()) / "streamlit-geospatial-matplotlib"),
)

import matplotlib.pyplot as plt
import numpy as np
import rasterio
from rasterio.io import MemoryFile
import streamlit as st


st.set_page_config(page_title="Raster analysis", page_icon="🛰️", layout="wide")
st.title("Raster analysis")
st.caption("Inspect raster metadata, visualize individual bands, and calculate sample statistics.")

source_mode = st.radio("Data source", ("Bundled elevation sample", "Upload GeoTIFF"), horizontal=True)
uploaded = None
if source_mode == "Upload GeoTIFF":
    uploaded = st.file_uploader("Upload a GeoTIFF", type=["tif", "tiff"])
    if uploaded is None:
        st.info("Upload a GeoTIFF to begin.")
        st.stop()

try:
    memory_file = MemoryFile(uploaded.getvalue()) if uploaded else nullcontext()
    with memory_file as memory:
        dataset_context = memory.open() if uploaded else rasterio.open(
            Path("data/ALPSMLC30_N021E039_DSM.tif")
        )
        with dataset_context as dataset:
            band_number = st.selectbox("Band", range(1, dataset.count + 1))
            scale = min(1.0, 1200 / max(dataset.width, dataset.height))
            output_height = max(1, int(dataset.height * scale))
            output_width = max(1, int(dataset.width * scale))
            band = dataset.read(
                band_number,
                out_shape=(output_height, output_width),
                masked=True,
            )
            values = band.compressed()
            if values.size == 0:
                raise ValueError("The selected band contains no valid pixels.")

            metrics = st.columns(4)
            metrics[0].metric("Width", f"{dataset.width:,} px")
            metrics[1].metric("Height", f"{dataset.height:,} px")
            metrics[2].metric("Bands", dataset.count)
            metrics[3].metric("CRS", str(dataset.crs or "Unknown"))

            image_column, details_column = st.columns((3, 2))
            with image_column:
                st.subheader("Band preview")
                lower, upper = np.percentile(values, [2, 98])
                figure, axis = plt.subplots(figsize=(10, 7))
                image = axis.imshow(band, cmap="terrain", vmin=lower, vmax=upper)
                axis.set_axis_off()
                figure.colorbar(image, ax=axis, shrink=0.75, label=f"Band {band_number} value")
                st.pyplot(figure, width="stretch")
                plt.close(figure)

            with details_column:
                st.subheader("Metadata")
                st.json(
                    {
                        "driver": dataset.driver,
                        "dtype": dataset.dtypes[band_number - 1],
                        "nodata": dataset.nodata,
                        "bounds": {
                            "left": dataset.bounds.left,
                            "bottom": dataset.bounds.bottom,
                            "right": dataset.bounds.right,
                            "top": dataset.bounds.top,
                        },
                        "pixel_size": {
                            "x": abs(dataset.transform.a),
                            "y": abs(dataset.transform.e),
                        },
                    }
                )
                st.subheader("Sample statistics")
                st.dataframe(
                    {
                        "Statistic": ["Minimum", "Maximum", "Mean", "Median", "Std. deviation"],
                        "Value": [
                            float(values.min()),
                            float(values.max()),
                            float(values.mean()),
                            float(np.median(values)),
                            float(values.std()),
                        ],
                    },
                    hide_index=True,
                    width="stretch",
                )

            st.subheader("Value distribution")
            histogram, axis = plt.subplots(figsize=(12, 3.5))
            axis.hist(values, bins=60, color="#1769aa", alpha=0.85)
            axis.set_xlabel("Pixel value")
            axis.set_ylabel("Frequency")
            axis.grid(alpha=0.2)
            st.pyplot(histogram, width="stretch")
            plt.close(histogram)
except Exception as exc:
    st.error(f"Could not analyze the raster: {exc}")
