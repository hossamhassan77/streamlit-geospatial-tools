# Streamlit Geospatial Tools

An interactive Streamlit application for exploring vector and raster geospatial data.

## Features

- Load bundled datasets, uploaded files, or public URLs.
- Read CSV, XLSX, GeoJSON, GeoPackage, KML, and zipped Shapefiles.
- Detect latitude and longitude columns and convert tables to point layers.
- Display points, lines, and polygons on Folium maps.
- Filter categorical, Boolean, date, and numeric attributes.
- Export clean CSV files without internal geometry or index columns.
- Inspect GeoTIFF metadata, bands, statistics, previews, and histograms.
- Calculate geometry measurements, create metric buffers, and dissolve features.
- Configure PostgreSQL/PostGIS lazily through environment variables.

## Requirements

- Python 3.10 or newer
- A C-compatible geospatial Python environment supported by GeoPandas and Rasterio

Do not commit or reuse the included `streamvenv` directory. Virtual environments contain
machine-specific interpreter paths and should be recreated on every computer.

## Installation

```powershell
git clone https://github.com/hossamhassan77/streamlit-geospatial-tools.git
cd streamlit-geospatial-tools
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Copy `.env.example` to `.env` only when PostGIS or GeoServer settings are needed.

## Run

```powershell
streamlit run Home.py
```

Open `http://localhost:8501` if Streamlit does not open a browser automatically.

## Pages

1. **Vector data visualization** maps vector files and coordinate tables.
2. **Data manipulation** adds robust attribute filtering and filtered export.
3. **Raster analysis** previews raster bands and reports metadata and statistics.
4. **Analytical tools** provides measurements, buffers, and dissolve operations.

## Testing

```powershell
python -m unittest discover -s tests -v
python -m py_compile Home.py app_components.py geospatial_utils.py vector_page.py
```

## Security and Data Handling

- Uploaded archives are checked for path traversal and excessive extracted size.
- Popup values are HTML-escaped.
- Database connections are created only when explicitly requested.
- Uploaded files are processed in temporary directories and removed afterward.

## Limitations

- KML support depends on the GDAL/Fiona build installed on the host.
- Folium basemaps require internet access, although bundled datasets can load offline.
- Very large point layers are capped at 5,000 rendered markers to protect browser performance.
- Global buffer distances are approximate because buffering requires a projected CRS.
