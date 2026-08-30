import { useEffect, useState } from "react";

import "./AnalysisLoading.css";

const STATUS_MESSAGES = [
  "Comparing regional benchmarks...",
  "Assessing your current water intensity...",
  "Evaluating water-saving strategies...",
  "Building your recommended plan...",
  "Preparing your water-use projection...",
];

const STAGES = ["BENCHMARK", "STRATEGIES", "PROJECTION"];

export default function AnalysisLoading() {
  const [statusIndex, setStatusIndex] = useState(0);

  useEffect(() => {
    const interval = window.setInterval(() => {
      setStatusIndex((current) => (current + 1) % STATUS_MESSAGES.length);
    }, 1500);

    return () => window.clearInterval(interval);
  }, []);

  const activeStage = statusIndex % STAGES.length;

  return (
    <div
      className="analysis-loading"
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <div className="analysis-ripple" aria-hidden="true">
        <span className="ripple-ring" />
        <span className="ripple-ring" />
        <span className="ripple-ring" />
        <span className="ripple-core" />
      </div>

      <p className="analysis-kicker">ANALYSING YOUR WATER USE</p>

      <p className="analysis-copy">
        Comparing your farm with regional benchmarks and evaluating
        water-saving strategies.
      </p>

      <p className="analysis-status">{STATUS_MESSAGES[statusIndex]}</p>

      <div className="analysis-shimmer" aria-hidden="true">
        <span />
      </div>

      <div className="analysis-stages" aria-hidden="true">
        {STAGES.map((stage, index) => (
          <span key={stage}>
            <strong className={index === activeStage ? "active" : ""}>
              {stage}
            </strong>
            {index < STAGES.length - 1 && (
              <span className="stage-arrow">→</span>
            )}
          </span>
        ))}
      </div>
    </div>
  );
}
