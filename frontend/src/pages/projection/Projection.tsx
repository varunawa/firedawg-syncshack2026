import { useState } from "react";

import "./Projection.css";

import {
  type BackendStrategy,
  type ProjectionTimelinePoint,
  type WaterProjection,
} from "../suggestions/Suggestions";

interface ProjectionProps {
  projection?: WaterProjection | null;
  selectedStrategies?: BackendStrategy[];
}

function formatIntensity(value: number) {
  return value.toFixed(2);
}

function formatMl(value: number) {
  return value.toLocaleString("en-AU", {
    maximumFractionDigits: 2,
  });
}

function formatAud(value: number) {
  return `$${Math.round(value).toLocaleString("en-AU")}`;
}

function formatPercent(value: number) {
  return Number.isInteger(value)
    ? `${value}`
    : value.toFixed(1);
}

function IntensityChart({
  timeline,
}: {
  timeline: ProjectionTimelinePoint[];
}) {
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  const width = 800;
  const height = 320;
  const pad = { l: 58, r: 24, t: 24, b: 44 };
  const innerW = width - pad.l - pad.r;
  const innerH = height - pad.t - pad.b;

  const values = timeline.map(
    (point) => point.projected_water_intensity_ml_per_ha
  );
  const minY = Math.min(...values);
  const maxY = Math.max(...values);
  const range = maxY - minY || 1;
  const y0 = minY - range * 0.12;
  const y1 = maxY + range * 0.12;

  const x = (month: number) =>
    pad.l + (month / 12) * innerW;

  const y = (value: number) =>
    pad.t + (1 - (value - y0) / (y1 - y0)) * innerH;

  const path = timeline
    .map((point, index) => {
      const command = index === 0 ? "M" : "L";
      return `${command} ${x(point.month)} ${y(
        point.projected_water_intensity_ml_per_ha
      )}`;
    })
    .join(" ");

  const ticks = [0, 3, 6, 9, 12];
  const yTicks = [y0, (y0 + y1) / 2, y1];
  const hovered =
    hoverIndex != null ? timeline[hoverIndex] : null;

  return (
    <div className="projection-chart-wrap">
      <svg
        className="projection-chart"
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label="Projected water intensity over 12 months"
      >
        {yTicks.map((tick) => (
          <g key={tick}>
            <line
              className="chart-grid"
              x1={pad.l}
              x2={width - pad.r}
              y1={y(tick)}
              y2={y(tick)}
            />
            <text
              className="chart-label"
              x={pad.l - 10}
              y={y(tick) + 4}
              textAnchor="end"
            >
              {formatIntensity(tick)}
            </text>
          </g>
        ))}

        {ticks.map((month) => (
          <text
            key={month}
            className="chart-label"
            x={x(month)}
            y={height - 14}
            textAnchor="middle"
          >
            {month}
          </text>
        ))}

        <text
          className="chart-axis-title"
          x={18}
          y={height / 2}
          textAnchor="middle"
          transform={`rotate(-90 18 ${height / 2})`}
        >
          Water intensity (ML/ha)
        </text>

        <text
          className="chart-axis-title"
          x={pad.l + innerW / 2}
          y={height - 2}
          textAnchor="middle"
        >
          Months
        </text>

        <path className="chart-line" d={path} fill="none" />

        {timeline.map((point, index) => (
          <circle
            key={point.month}
            className={
              hoverIndex === index
                ? "chart-point active"
                : "chart-point"
            }
            cx={x(point.month)}
            cy={y(point.projected_water_intensity_ml_per_ha)}
            r={hoverIndex === index ? 7 : 5.5}
            onMouseEnter={() => setHoverIndex(index)}
            onMouseLeave={() => setHoverIndex(null)}
          />
        ))}
      </svg>

      {hovered && (
        <div className="chart-tooltip">
          <strong>Month {hovered.month}</strong>
          <p>
            Projected intensity
            <span>
              {formatIntensity(
                hovered.projected_water_intensity_ml_per_ha
              )}{" "}
              ML/ha
            </span>
          </p>
          <p>
            Cumulative water saved
            <span>
              {formatMl(hovered.cumulative_water_saved_ml)} ML
            </span>
          </p>
          <p>
            Cumulative saving / ha
            <span>
              {formatIntensity(
                hovered.cumulative_water_saved_ml_per_ha
              )}{" "}
              ML/ha
            </span>
          </p>
        </div>
      )}
    </div>
  );
}

function SavingsChart({
  timeline,
}: {
  timeline: ProjectionTimelinePoint[];
}) {
  const width = 800;
  const height = 160;
  const pad = { l: 58, r: 24, t: 16, b: 36 };
  const innerW = width - pad.l - pad.r;
  const innerH = height - pad.t - pad.b;
  const values = timeline.map(
    (point) => point.cumulative_water_saved_ml
  );
  const maxY = Math.max(...values, 1);

  const x = (month: number) =>
    pad.l + (month / 12) * innerW;
  const y = (value: number) =>
    pad.t + (1 - value / maxY) * innerH;

  const path = timeline
    .map((point, index) => {
      const command = index === 0 ? "M" : "L";
      return `${command} ${x(point.month)} ${y(
        point.cumulative_water_saved_ml
      )}`;
    })
    .join(" ");

  return (
    <svg
      className="projection-chart savings-chart"
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-label="Cumulative water saved over 12 months"
    >
      <line
        className="chart-grid"
        x1={pad.l}
        x2={width - pad.r}
        y1={y(0)}
        y2={y(0)}
      />
      <line
        className="chart-grid"
        x1={pad.l}
        x2={width - pad.r}
        y1={y(maxY)}
        y2={y(maxY)}
      />
      <text className="chart-label" x={pad.l - 10} y={y(0) + 4} textAnchor="end">
        0
      </text>
      <text className="chart-label" x={pad.l - 10} y={y(maxY) + 4} textAnchor="end">
        {formatMl(maxY)}
      </text>
      {[0, 3, 6, 9, 12].map((month) => (
        <text
          key={month}
          className="chart-label"
          x={x(month)}
          y={height - 10}
          textAnchor="middle"
        >
          {month}
        </text>
      ))}
      <path className="chart-line savings-line" d={path} fill="none" />
      {timeline.map((point) => (
        <circle
          key={point.month}
          className="chart-point savings-point"
          cx={x(point.month)}
          cy={y(point.cumulative_water_saved_ml)}
          r={4.5}
        />
      ))}
    </svg>
  );
}

export default function Projection({
  projection = null,
  selectedStrategies = [],
}: ProjectionProps) {
  const timeline = projection?.timeline ?? [];
  const hasTimeline = timeline.length > 0;

  if (!projection || !hasTimeline) {
    return (
      <section className="projection-page">
        <div className="projection-empty">
          <p className="projection-kicker">
            12-MONTH ESTIMATED PROJECTION
          </p>
          <h2>Projection data is not available for this recommendation plan.</h2>
          <p>
            Try adjusting the annual budget on Suggestions, then return to this
            view.
          </p>
        </div>
      </section>
    );
  }

  return (
    <section className="projection-page">
      <header className="projection-header">
        <p className="projection-kicker">
          12-MONTH ESTIMATED PROJECTION
        </p>
        <h1>
          See how your water use could change over the next 12 months if the
          recommended strategy plan is implemented.
        </h1>
        <p className="projection-note">
          This projection estimates the combined effect of the
          optimiser-selected strategies. Annual savings are assumed to
          accumulate evenly over the 12-month period.
        </p>
      </header>

      <div className="projection-hero">
        <div>
          <span>Current water intensity</span>
          <strong>
            {formatIntensity(projection.current_water_intensity_ml_per_ha)}
            <small> ML/ha</small>
          </strong>
        </div>
        <span className="projection-arrow">→</span>
        <div>
          <span>Projected water intensity</span>
          <strong>
            {formatIntensity(projection.projected_water_intensity_ml_per_ha)}
            <small> ML/ha</small>
          </strong>
        </div>
        <div className="projection-reduction">
          <strong>
            {formatPercent(projection.reduction_percent)}%
          </strong>
          <span>Expected reduction</span>
        </div>
      </div>

      <div className="projection-card">
        <p className="projection-kicker">PROJECTED WATER INTENSITY</p>
        <IntensityChart timeline={timeline} />
      </div>

      <div className="projection-card">
        <p className="projection-kicker">CUMULATIVE WATER SAVED</p>
        <SavingsChart timeline={timeline} />
      </div>

      <div className="projection-metrics">
        <div>
          <span>Annual water saving</span>
          <strong>
            {formatMl(projection.annual_water_saved_ml)} ML
          </strong>
        </div>
        <div>
          <span>Saving per hectare</span>
          <strong>
            {formatIntensity(projection.annual_water_saved_ml_per_ha)}{" "}
            ML/ha
          </strong>
        </div>
        <div>
          <span>Annual strategy cost</span>
          <strong>{formatAud(projection.annual_cost_aud)}</strong>
        </div>
        <div>
          <span>Cost per ML saved</span>
          <strong>
            {projection.cost_per_ml_saved_aud != null
              ? `${formatAud(projection.cost_per_ml_saved_aud)} / ML`
              : "—"}
          </strong>
        </div>
      </div>

      {selectedStrategies.length > 0 && (
        <div className="projection-plan">
          <p className="projection-kicker">
            BASED ON YOUR RECOMMENDED PLAN
          </p>
          <p className="projection-plan-count">
            {selectedStrategies.length}{" "}
            {selectedStrategies.length === 1
              ? "strategy selected"
              : "strategies selected"}
          </p>
          <div className="projection-pills">
            {selectedStrategies.map((strategy) => (
              <span key={strategy.id}>{strategy.name}</span>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
