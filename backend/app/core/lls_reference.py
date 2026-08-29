# Maps Local Land Services agricultural selections directly to valley 

LLS_REGION_TO_VALLEY = {
    "central_tablelands":  "lachlan",
    "central_west":        "macquarie",
    "greater_sydney":      "murray",  # Fallback to high availability asset rule
    "hunter":              "murray",  # Fallback to high availability asset rule
    "murray":              "murray",
    "north_coast":         "murray",  # Fallback to high availability asset rule
    "north_west_nsw":      "namoi",
    "northern_tablelands":  "gwydir",
    "riverina":            "murrumbidgee",
    "south_east_nsw":      "murray",  # Fallback to high availability asset rule
    "western":             "lower_darling"
}

def get_allocation_by_lls(lls_name: str, telemetry_db: dict):
    """
    Looks up LLS string inputs and extracts the corresponding live water parameters
    """
    clean_key = lls_name.strip().lower().replace(" ", "_")
    valley_key = LLS_REGION_TO_VALLEY.get(clean_key)
    
    if not valley_key:
        return {"error": "Selected agricultural zone sits outside core mapping layers"}
        
    return telemetry_db.get(valley_key)