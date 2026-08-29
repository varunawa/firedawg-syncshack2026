from app.schemas import ProjectionPoint, ProjectionResult


def build_projection(
    current_water_intensity_ml_per_ha: float,
    projected_water_intensity_ml_per_ha: float,
    total_estimated_savings_ml: float,
    total_annual_cost_aud: float,
    cost_per_ml_saved_aud: float | None,
    land_area_ha: float,
) -> ProjectionResult:

    annual_saved_per_ha = (
        current_water_intensity_ml_per_ha
        - projected_water_intensity_ml_per_ha
    )

    reduction_percent = (
        annual_saved_per_ha / current_water_intensity_ml_per_ha * 100
        if current_water_intensity_ml_per_ha > 0
        else 0
    )

    timeline = []

    for month in [0, 3, 6, 9, 12]:
        fraction = month / 12

        projected_intensity = (
            current_water_intensity_ml_per_ha
            - annual_saved_per_ha * fraction
        )

        cumulative_saved_ml = (
            total_estimated_savings_ml * fraction
        )

        cumulative_saved_per_ha = (
            cumulative_saved_ml / land_area_ha
            if land_area_ha > 0
            else 0
        )

        timeline.append(
            ProjectionPoint(
                month=month,
                projected_water_intensity_ml_per_ha=round(
                    projected_intensity, 3
                ),
                cumulative_water_saved_ml=round(
                    cumulative_saved_ml, 3
                ),
                cumulative_water_saved_ml_per_ha=round(
                    cumulative_saved_per_ha, 3
                ),
            )
        )

    return ProjectionResult(
        current_water_intensity_ml_per_ha=round(
            current_water_intensity_ml_per_ha, 3
        ),
        projected_water_intensity_ml_per_ha=round(
            projected_water_intensity_ml_per_ha, 3
        ),
        annual_water_saved_ml=round(
            total_estimated_savings_ml, 3
        ),
        annual_water_saved_ml_per_ha=round(
            annual_saved_per_ha, 3
        ),
        reduction_percent=round(
            reduction_percent, 2
        ),
        annual_cost_aud=round(
            total_annual_cost_aud, 2
        ),
        cost_per_ml_saved_aud=(
            round(cost_per_ml_saved_aud, 2)
            if cost_per_ml_saved_aud is not None
            else None
        ),
        timeline=timeline,
    )