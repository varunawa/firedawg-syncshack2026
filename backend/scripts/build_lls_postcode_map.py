import os
import json
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POSTCODE_CSV_PATH = os.path.join(BASE_DIR, "..", "australian_postcodes.csv")
OUTPUT_JSON_PATH = os.path.join(BASE_DIR, "..", "postcode_lls_map.json")

# Strict, definitive numeric mapping indices for NSW Local Land Services
LLS_RANGE_MATRIX = [
    # 1. Murray LLS Core
    (2640, 2647, "murray"), (2710, 2714, "murray"), (2731, 2736, "murray"), (3644, 3644, "murray"), (3691, 3691, "murray"),
    # 2. Riverina LLS Core
    (2590, 2590, "riverina"), (2650, 2652, "riverina"), (2655, 2661, "riverina"), (2663, 2663, "riverina"), (2665, 2666, "riverina"), (2700, 2707, "riverina"), (2715, 2716, "riverina"), (2678, 2678, "riverina"),
    # 3. Central West LLS Core
    (2795, 2795, "central_west"), (2798, 2798, "central_west"), (2800, 2800, "central_west"), (2820, 2823, "central_west"), (2830, 2831, "central_west"), (2842, 2844, "central_west"), (2866, 2871, "central_west"), (2873, 2876, "central_west"),
    # 4. North West LLS Core
    (2338, 2347, "north_west_nsw"), (2379, 2382, "north_west_nsw"), (2386, 2390, "north_west_nsw"), (2397, 2398, "north_west_nsw"), (2400, 2406, "north_west_nsw"), (2411, 2411, "north_west_nsw"),
    # 5. Northern Tablelands LLS Core
    (2350, 2355, "northern_tablelands"), (2358, 2361, "northern_tablelands"), (2365, 2372, "northern_tablelands"),
    # 6. Western LLS Core
    (2835, 2840, "western"), (2877, 2880, "western"),
    # 7. South East LLS Core (Including ACT)
    (200, 200, "south_east_nsw"), (2546, 2551, "south_east_nsw"), (2584, 2584, "south_east_nsw"), (2600, 2617, "south_east_nsw"), (2619, 2621, "south_east_nsw"), (2623, 2633, "south_east_nsw"), (2730, 2730, "south_east_nsw"), (2900, 2914, "south_east_nsw"),
    # 8. Hunter LLS Core
    (2259, 2259, "hunter"), (2265, 2265, "hunter"), (2291, 2294, "hunter"), (2296, 2305, "hunter"), (2307, 2308, "hunter"), (2321, 2322, "hunter"), (2325, 2327, "hunter"), (2333, 2335, "hunter"), (2421, 2421, "hunter"), (2849, 2849, "hunter"),
    # 9. North Coast LLS Core
    (2429, 2429, "north_coast"), (2439, 2440, "north_coast"), (2444, 2446, "north_coast"), (2450, 2453, "north_coast"), (2456, 2456, "north_coast"), (2462, 2466, "north_coast"), (2470, 2472, "north_coast"), (2474, 2474, "north_coast"), (2477, 2477, "north_coast"), (2482, 2483, "north_coast"), (2485, 2490, "north_coast")
]

def main():
    print("🔄 Standardising and range-filtering raw postcode assets...")
    df = pd.read_csv(POSTCODE_CSV_PATH, dtype={"postcode": str})
    
    compiled_output = []
    
    for _, row in df.iterrows():
        pcode_str = str(row["postcode"]).zfill(4)
        state_val = str(row.get("state", "UNKNOWN")).upper().strip()
        locality_val = str(row.get("locality", "UNKNOWN")).upper().strip()
        
        # Guard clause: only evaluate NSW/ACT for LLS boundaries
        if state_val not in ["NSW", "ACT"]:
            continue
            
        pcode_int = int(pcode_str)
        lls_slug = None
        
        # 1. Evaluate explicit numeric matrix ranges
        for start, end, slug in LLS_RANGE_MATRIX:
            if start <= pcode_int <= end:
                lls_slug = slug
                break
                
        # 2. If range misses, evaluate spatial keyword defaults
        if not lls_slug:
            lga_clean = str(row.get("lgaregion", "")).lower()
            if "wagga" in lga_clean or "griffith" in lga_clean: lls_slug = "riverina"
            elif "albury" in lga_clean or "deniliquin" in lga_clean: lls_slug = "murray"
            elif "dubbo" in lga_clean or "orange" in lga_clean: lls_slug = "central_west"
            else: lls_slug = "greater_sydney" # True default for unassigned metro elements

        display_name = lls_slug.replace("_", " ").title().replace("Nsw", "NSW")
        
        compiled_output.append({
            "postcode": pcode_str,
            "suburb": locality_val,
            "state": state_val,
            "lls_region_id": lls_slug,
            "lls_region_name": display_name
        })

    final_df = pd.DataFrame(compiled_output).drop_duplicates(subset=["postcode", "suburb"])
    
    with open(OUTPUT_JSON_PATH, "w") as f:
        json.dump(final_df.to_dict(orient="records"), f, indent=2)
        
    print(f"✅ Safe lookup generated containing {len(final_df)} validated rows.")

if __name__ == "__main__":
    main()
