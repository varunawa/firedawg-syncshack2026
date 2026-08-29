import { useState } from "react";
import "./Scenarios.css";
import Suggestions, {
  type Suggestion,
  type BusinessData,
} from "../suggestions/Suggestions";

export interface BenchmarkResult {
  benchmark_water_intensity_ml_per_ha: number | null;
  benchmark_year: string | null;
  crop_category: string;
  delta_pct: number | null;
  is_state_fallback: boolean;
  lls_region: string | null;
  mean_ml_per_ha: number | null;
  note: string | null;
  percentile: number | null;
  rating: string;
  region_used: string | null;
  sample_size: number | null;
  stdev_ml_per_ha: number | null;
  user_water_intensity_ml_per_ha: number;
  z_score: number | null;
  water_source: string | null;
  water_allocation_pct_vs_historic: number | null;
  weather_status: string | null;
  weather_summary: {
    seven_day_rainfall_mm?: number | null;
    climatic_water_deficit_mm?: number | null;
  } | null;
}

interface ScenarioProps {
  benchmark: BenchmarkResult;
  summary?: string | null;
  summaryLoading?: boolean;
  suggestions: Suggestion[];
  businessData?: BusinessData | null;
  onEditDetails?: () => void;
}

type View =
  | "snapshot"
  | "position"
  | "peers"
  | "suggestions";

type RatingTier = "low" | "moderate" | "high" | "unknown";

function getRatingTier(rating: string): RatingTier {
  const normalized = rating.toLowerCase();

  if (normalized.includes("high")) {
    return "high";
  }

  if (
    normalized.includes("efficient") ||
    normalized.includes("low")
  ) {
    return "low";
  }

  if (
    normalized.includes("typical") ||
    normalized.includes("moderate")
  ) {
    return "moderate";
  }

  return "unknown";
}

const views: View[] = [
  "snapshot",
  "position",
  "peers",
  "suggestions",
];

export default function Scenarios({
  benchmark,
  summary,
  summaryLoading,
  suggestions,
  businessData,
  onEditDetails,
}: ScenarioProps) {
    console.log(
    "SCENARIOS RECEIVED SUGGESTIONS:",
    suggestions
  );
  const [activeView, setActiveView] =
    useState<View>("snapshot");

  const ratingTier = getRatingTier(benchmark.rating);

  const currentUse =
    benchmark.user_water_intensity_ml_per_ha;

  const regionalBenchmark =
    benchmark.benchmark_water_intensity_ml_per_ha;

  const currentIndex = views.indexOf(activeView);

  const goNext = () => {
    if (currentIndex < views.length - 1) {
      setActiveView(views[currentIndex + 1]);
    }
  };

  const goBack = () => {
    if (currentIndex > 0) {
      setActiveView(views[currentIndex - 1]);
    }
  };

  const maxScale =
    Math.max(
      currentUse,
      regionalBenchmark ?? 0,
      1
    ) * 1.35;

  const userPosition = Math.min(
    Math.max((currentUse / maxScale) * 100, 5),
    95
  );

  const benchmarkPosition =
    regionalBenchmark !== null
      ? Math.min(
          Math.max(
            (regionalBenchmark / maxScale) * 100,
            5
          ),
          95
        )
      : null;

  const differenceText =
    benchmark.delta_pct !== null
      ? `${Math.abs(benchmark.delta_pct)}% ${
          benchmark.delta_pct < 0
            ? "below"
            : benchmark.delta_pct > 0
              ? "above"
              : "at"
        } benchmark`
      : "Comparison unavailable";

  const percentilePosition =
    benchmark.percentile !== null
      ? Math.min(
          Math.max(benchmark.percentile, 5),
          95
        )
      : 50;

  const allocationValue =
    benchmark.water_allocation_pct_vs_historic != null &&
    Number.isFinite(benchmark.water_allocation_pct_vs_historic)
      ? benchmark.water_allocation_pct_vs_historic
      : null;

  const allocationText =
    allocationValue !== null
      ? `${Math.abs(allocationValue).toFixed(1)}% ${
          allocationValue < 0 ? "below" : "above"
        } historic`
      : "Historic allocation unavailable";

  const weatherText =
    benchmark.weather_status
      ? benchmark.weather_status.charAt(0).toUpperCase() + benchmark.weather_status.slice(1)
      : "Weather unavailable";

  const rainfallMm =
    benchmark.weather_summary?.seven_day_rainfall_mm != null &&
    Number.isFinite(benchmark.weather_summary.seven_day_rainfall_mm)
      ? benchmark.weather_summary.seven_day_rainfall_mm
      : null;
  const deficitMm =
    benchmark.weather_summary?.climatic_water_deficit_mm != null &&
    Number.isFinite(benchmark.weather_summary.climatic_water_deficit_mm)
      ? benchmark.weather_summary.climatic_water_deficit_mm
      : null;

  return (
    <main
        className={`scenarios${
          activeView === "suggestions"
            ? " suggestions-active"
            : ""
        }`}
  >
        <button
            type="button"
            onClick={onEditDetails}
            className="edit-details-button"
            >
            ↻ Edit farm details
        </button>
      <div className="scenario-shell">

        {/* TOP NAVIGATION */}
        <header className="scenario-header">
          <div className="scenario-brand">
            <span className="brand-dot" />
            H2.OS
          </div>

          <div className="scenario-tabs">
            <button
              className={
                activeView === "snapshot"
                  ? "scenario-tab active"
                  : "scenario-tab"
              }
              onClick={() =>
                setActiveView("snapshot")
              }
            >
              Snapshot
            </button>

            <button
              className={
                activeView === "position"
                  ? "scenario-tab active"
                  : "scenario-tab"
              }
              onClick={() =>
                setActiveView("position")
              }
            >
              Water Position
            </button>

            <button
              className={
                activeView === "peers"
                  ? "scenario-tab active"
                  : "scenario-tab"
              }
              onClick={() =>
                setActiveView("peers")
              }
            >
              Peer Comparison
            </button>

            <button
              className={
                activeView === "suggestions"
                  ? "scenario-tab active"
                  : "scenario-tab"
              }
              onClick={() =>
                setActiveView("suggestions")
              }
            >
              Suggestions
            </button>
          </div>
        </header>

        {/* SNAPSHOT */}
        {activeView === "snapshot" && (
          <section className="scenario-view snapshot-view">
            <div className="view-content narrow">
              <p className="scenario-label">
                YOUR WATER SNAPSHOT
              </p>

              <h1>
                Here's what your water data tells
                us about your farm.
              </h1>

              {summaryLoading ? (
                <p className="hero-summary">
                  Generating your personalised
                  water summary…
                </p>
              ) : summary ? (
                <p className="hero-summary">
                  {summary}
                </p>
              ) : (
                <p className="hero-summary">
                  We've analysed your water use
                  against agricultural and regional
                  benchmarks to give you a clearer
                  picture of your current position.
                </p>
              )}

              <div
                className={`snapshot-rating rating-${ratingTier}`}
              >
                <span>Overall rating</span>

                <strong>
                  {benchmark.rating}
                </strong>
              </div>

              <div className="snapshot-numbers">
                <div>
                  <span>Your water use</span>

                  <strong>
                    {currentUse.toFixed(1)}
                    <small> ML/ha</small>
                  </strong>
                </div>

                <div className="snapshot-divider" />

                <div>
                  <span>Regional benchmark</span>

                  <strong>
                    {regionalBenchmark !== null
                      ? regionalBenchmark.toFixed(1)
                      : "N/A"}

                    {regionalBenchmark !== null && (
                      <small> ML/ha</small>
                    )}
                  </strong>
                </div>
              </div>

              <div className="snapshot-context-grid">
                <div className="mini-metric">
                  <span>Water source</span>
                  <strong>{benchmark.water_source || "N/A"}</strong>
                </div>

                <div className="snapshot-divider" />

                <div className="mini-metric">
                  <span>Allocation</span>
                  <strong>{allocationText}</strong>
                </div>

                <div className="snapshot-divider" />

                <div className="mini-metric">
                  <span>Weather</span>
                  <strong>
                    {weatherText}
                    {rainfallMm !== null && (
                      <small> · {rainfallMm.toFixed(1)} mm rain</small>
                    )}
                  </strong>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* WATER POSITION */}
        {activeView === "position" && (
          <section className="scenario-view">
            <div className="view-content">
              <p className="scenario-label">
                YOUR WATER POSITION
              </p>

              <h2>
                See where your farm sits.
              </h2>

              <p className="section-description">
                Compare your current water
                application rate with the regional
                benchmark for{" "}
                {benchmark.crop_category}.
              </p>

              <div className="glass-card water-position-card">
                <div className="position-heading">
                  <div>
                    <span className="metric-label">
                      Your water use
                    </span>

                    <strong className="large-number">
                      {currentUse.toFixed(1)}
                      <small> ML/ha</small>
                    </strong>
                  </div>

                  <div
                    className={`difference-pill rating-${ratingTier}`}
                  >
                    {differenceText}
                  </div>
                </div>

                <div className="water-scale">
                  <div className="scale-track" />

                  <div
                    className={`scale-marker user-marker rating-${ratingTier}`}
                    style={{
                      left: `${userPosition}%`,
                    }}
                  >
                    <div className="user-dot" />

                    <div className="scale-label">
                      <span>You</span>

                      <strong>
                        {currentUse.toFixed(1)}
                      </strong>
                    </div>
                  </div>

                  {benchmarkPosition !== null && (
                    <div
                      className="scale-marker benchmark-marker"
                      style={{
                        left: `${benchmarkPosition}%`,
                      }}
                    >
                      <div className="benchmark-line" />

                      <div className="scale-label">
                        <span>Benchmark</span>

                        <strong>
                          {regionalBenchmark?.toFixed(
                            1
                          )}
                        </strong>
                      </div>
                    </div>
                  )}
                </div>

                <div className="scale-direction">
                  <span>Lower water use</span>
                  <span>Higher water use</span>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* PEER COMPARISON */}
        {activeView === "peers" && (
          <section className="scenario-view">
            <div className="view-content">
              <p className="scenario-label">
                PEER COMPARISON
              </p>

              <h2>
                How do you compare?
              </h2>

              <p className="section-description">
                See where your water application
                rate sits compared with similar
                observations in the dataset.
              </p>

              <div className="glass-card percentile-card">
                <div className="distribution-wrapper">
                  <svg
                    className="distribution-curve"
                    viewBox="0 0 800 300"
                    preserveAspectRatio="none"
                    aria-hidden="true"
                  >
                    <path
                      d="
                        M20 260
                        C120 255, 145 230, 200 180
                        C260 125, 300 55, 400 50
                        C500 55, 540 125, 600 180
                        C655 230, 680 255, 780 260
                      "
                    />
                  </svg>

                  {benchmark.percentile !== null && (
                    <div
                      className={`peer-marker rating-${ratingTier}`}
                      style={{
                        left: `${percentilePosition}%`,
                      }}
                    >
                      <div className="peer-line" />
                      <div className="peer-dot" />
                      <span>You</span>
                    </div>
                  )}
                </div>

                <div className="percentile-result">
                  <span>Your position</span>

                  <strong>
                    {benchmark.percentile !== null
                      ? `${benchmark.percentile}th`
                      : "N/A"}
                  </strong>

                  <p>percentile</p>
                </div>

                <div className="peer-context">
                  <div>
                    <span>Compared with</span>

                    <strong>
                      {benchmark.sample_size ??
                        "N/A"}{" "}
                      observations
                    </strong>
                  </div>

                  <div>
                    <span>Region</span>

                    <strong>
                      {benchmark.region_used ??
                        "NSW"}
                    </strong>
                  </div>

                  <div>
                    <span>Crop</span>

                    <strong>
                      {benchmark.crop_category}
                    </strong>
                  </div>
                </div>
              </div>
            </div>
          </section>
        )}

        {/* SUGGESTIONS */}
        {activeView === "suggestions" && (
          <Suggestions
            suggestions={suggestions}
            currentWaterUse={currentUse}
            businessData={businessData}
            onBack={() =>
              setActiveView("peers")
            }
          />
        )}

        {/* BOTTOM NAV */}
        {activeView !== "suggestions" && (
          <footer className="scenario-navigation">
            <button
              className="nav-button secondary"
              onClick={goBack}
              disabled={currentIndex === 0}
            >
              ← Back
            </button>

            <div className="progress-dots">
              {views.map((view) => (
                <button
                  key={view}
                  aria-label={`Go to ${view}`}
                  className={
                    activeView === view
                      ? "progress-dot active"
                      : "progress-dot"
                  }
                  onClick={() =>
                    setActiveView(view)
                  }
                />
              ))}
            </div>

            <button
              className="nav-button primary"
              onClick={goNext}
            >
              Next →
            </button>
          </footer>
        )}
      </div>
    </main>
  );
}