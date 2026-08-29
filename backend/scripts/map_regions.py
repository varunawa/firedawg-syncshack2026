import os
import json
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

# Define correct relative paths from the backend/scripts/ directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POSTCODE_CSV_PATH = os.path.join(BASE_DIR, "..", "australian_postcodes.csv")
GEOJSON_PATH = os.path.join(BASE_DIR, "..", "cewo_mdb_valleys.geojson")
OUTPUT_JSON_PATH = os.path.join(BASE_DIR, "..", "postcode_map.json")

def main():
    print("Loading source map datasets into memory...")
    
    # Verify files exist before trying to read them
    if not os.path.exists(GEOJSON_PATH):
        print(f"Error: Cannot find GeoJSON map file at {os.path.normpath(GEOJSON_PATH)}")
        return
    if not os.path.exists(POSTCODE_CSV_PATH):
        print(f"Error: Cannot find Postcodes CSV file at {os.path.normpath(POSTCODE_CSV_PATH)}")
        return

    # 1. Load the official valley polygon vectors
    valleys = gpd.read_file(GEOJSON_PATH)

    # 2. Read the master list of all Australian postcodes
    df_postcodes = pd.read_csv(POSTCODE_CSV_PATH)

    # Clean up column spaces and lowercase everything to make it foolproof
    df_postcodes.columns = df_postcodes.columns.str.strip().str.lower()
    print(f"Detected CSV columns: {list(df_postcodes.columns)}")

    # 3. Dynamically find coordinate column variations (handles lat, latitude, lng, lon, longitude)
    lat_col = next((c for c in df_postcodes.columns if 'lat' in c), None)
    lon_col = next((c for c in df_postcodes.columns if 'lon' in c or 'lng' in c), None)

    if not lat_col or not lon_col:
        print(f"Error: Could not find coordinate columns in your CSV.")
        print(f"Available columns: {list(df_postcodes.columns)}")
        return

    # Drop rows missing coordinates using the dynamically detected columns
    initial_count = len(df_postcodes)
    df_postcodes = df_postcodes.dropna(subset=[lon_col, lat_col])
    
    # Dynamically find postcode, suburb, and state variations
    postcode_col = next((c for c in df_postcodes.columns if 'postcode' in c or 'pcode' in c), 'postcode')
    suburb_col = next((c for c in df_postcodes.columns if 'suburb' in c or 'place' in c or 'locality' in c), 'suburb')
    state_col = next((c for c in df_postcodes.columns if 'state' in c or 'territory' in c), 'state')

    # Standardize types and strings
    df_postcodes["postcode"] = df_postcodes[postcode_col].astype(str).str.zfill(4)
    df_postcodes["suburb"] = df_postcodes[suburb_col].astype(str).str.strip().str.upper()
    df_postcodes["state"] = df_postcodes[state_col].astype(str).str.strip().str.upper()

    print(f"Cleaned data: {len(df_postcodes)} / {initial_count} rows contain valid coordinates.")

    # 4. Map coordinates to spatial geometry points using our detected columns
    geometry = [Point(xy) for xy in zip(df_postcodes[lon_col], df_postcodes[lat_col])]
    geo_postcodes = gpd.GeoDataFrame(df_postcodes, geometry=geometry, crs="EPSG:4326")

    # 5. Synchronize spatial map alignments
    if geo_postcodes.crs != valleys.crs:
        valleys = valleys.to_crs(geo_postcodes.crs)

    print("⚡ Calculating spatial lookups (intersecting maps)... This can take a few seconds.")

    # 6. Spatial Join: Instantly check which valley polygon contains each coordinate point
    mapped_db = gpd.sjoin(geo_postcodes, valleys, how="inner", predicate="within")
    # Double-check the column properties provided by data.gov.au dataset
    valley_name_col = next((c for c in mapped_db.columns if 'valleyname' in c.lower()), None)
    if not valley_name_col:
        print("Error: Could not find 'ValleyName' column properties inside your GeoJSON file.")
        print(f"Available map attributes: {list(valleys.columns)}")
        return

    # 7. Format clean keys for your PixiJS engine layers using the exact column found
    mapped_db["VALLEY_NAME"] = mapped_db[valley_name_col]
    mapped_db["region_id"] = mapped_db["VALLEY_NAME"].astype(str).str.lower().str.replace(" ", "_").str.replace("-", "_")

    # 8. Filter down to primary dataset fields and drop duplicates
    output_fields = ["postcode", "suburb", "state", "region_id", "VALLEY_NAME"]
    final_df = mapped_db[output_fields].drop_duplicates(subset=["postcode", "suburb"])

    # 9. Save file output as JSON
    final_df.to_json(OUTPUT_JSON_PATH, orient="records", indent=2)

    print(f"Success! Generated lookup dataset containing {len(final_df)} coordinates inside the Basin footprint.")
    print(f"Saved directly to: {os.path.normpath(OUTPUT_JSON_PATH)}")

if __name__ == "__main__":
    main()
