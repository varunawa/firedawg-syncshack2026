import "./Scenarios.css";

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
}

interface ScenarioProps {
  benchmark: BenchmarkResult;
  summary?: string | null;
  summaryLoading?: boolean;
}

export default function Scenarios({
  benchmark,
  summary,
  summaryLoading,
}: ScenarioProps) {
  return (
    <section className="scenarios">
      <div className="scenario-container">
        <p className="scenario-label">H2.OS WATER ANALYSIS</p>

        <h1>Your water performance</h1>

        <div className="rating-card">
          <p>Overall Rating</p>
          <h2>{benchmark.rating}</h2>
        </div>

        {(summaryLoading || summary) && (
          <div className="scenario-summary">
            <p className="scenario-summary-label">What this means</p>
            {summaryLoading ? (
              <p className="scenario-summary-loading">
                Generating summary…
              </p>
            ) : (
              <p>{summary}</p>
            )}
          </div>
        )}

        <div className="scenario-grid">
          <div className="result-card">
            <span>Your water use</span>
            <strong>
              {benchmark.user_water_intensity_ml_per_ha} ML/ha
            </strong>
          </div>

          <div className="result-card">
            <span>Regional benchmark</span>
            <strong>
              {benchmark.benchmark_water_intensity_ml_per_ha ?? "N/A"} ML/ha
            </strong>
          </div>

          <div className="result-card">
            <span>Difference</span>
            <strong>
              {benchmark.delta_pct !== null
                ? `${benchmark.delta_pct > 0 ? "+" : ""}${benchmark.delta_pct}%`
                : "N/A"}
            </strong>
          </div>

          <div className="result-card">
            <span>Percentile</span>
            <strong>
              {benchmark.percentile !== null
                ? `${benchmark.percentile}%`
                : "N/A"}
            </strong>
          </div>
        </div>

        <div className="scenario-context">
          <p>
            <strong>Crop:</strong> {benchmark.crop_category}
          </p>

          <p>
            <strong>Region:</strong> {benchmark.region_used ?? "NSW"}
          </p>

          <p>
            <strong>Benchmark year:</strong>{" "}
            {benchmark.benchmark_year ?? "N/A"}
          </p>

          <p>
            <strong>Z-score:</strong>{" "}
            {benchmark.z_score ?? "N/A"}
          </p>
        </div>
      </div>
    </section>
  );
}