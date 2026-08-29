import httpx

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


async def geocode_location(place_name: str):
    """
    Convert a location like 'Griffith, NSW'
    into latitude and longitude.
    """

    params = {
        "name": place_name,
        "count": 1,
        "countryCode": "AU",
        "language": "en",
        "format": "json",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(GEOCODE_URL, params=params)
        response.raise_for_status()

    data = response.json()

    if not data.get("results"):
        raise ValueError(f'Could not find location "{place_name}"')

    location = data["results"][0]

    return {
        "name": location["name"],
        "region": location.get("admin1"),
        "latitude": location["latitude"],
        "longitude": location["longitude"],
    }


async def get_weather_data(latitude: float, longitude: float):
    """
    Get the 7-day agricultural weather outlook.
    """

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": ",".join([
            "precipitation_sum",
            "precipitation_probability_max",
            "et0_fao_evapotranspiration",
            "weather_code",
        ]),
        "timezone": "auto",
        "forecast_days": 7,
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(FORECAST_URL, params=params)
        response.raise_for_status()

    data = response.json()

    daily = data["daily"]

    forecast = []

    for i, date in enumerate(daily["time"]):
        forecast.append({
            "date": date,
            "rain_mm": daily["precipitation_sum"][i],
            "rain_probability_pct":
                daily["precipitation_probability_max"][i],
            "et0_mm":
                daily["et0_fao_evapotranspiration"][i],
            "weather_code":
                daily["weather_code"][i],
        })

    # useful H2.OS summaries
    total_rain = sum(
        day["rain_mm"] or 0
        for day in forecast
    )

    total_et0 = sum(
        day["et0_mm"] or 0
        for day in forecast
    )

    climatic_water_deficit = total_et0 - total_rain

    return {
        "forecast": forecast,
        "summary": {
            "seven_day_rainfall_mm": round(total_rain, 1),
            "seven_day_et0_mm": round(total_et0, 1),
            "climatic_water_deficit_mm":
                round(climatic_water_deficit, 1),
        },
    }


async def get_weather_for_location(place_name: str):
    """
    Main function used by H2.OS.
    """

    location = await geocode_location(place_name)

    weather = await get_weather_data(
        location["latitude"],
        location["longitude"],
    )

    return {
        "location": location,
        **weather,
    }