import {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import "./Suggestions.css";

/* =========================================================
   BACKEND TYPES
   ========================================================= */

export interface BackendStrategy {
  id: string;
  name: string;
  category: string;
  annual_cost_aud: number;
  estimated_savings_ml: number;
  savings_pct_applied: number;
  implementation_disruption: string;
  confidence: string;
  source: string;
}

export interface RecommendationResponse {
  risk: {
    z_score: number | null;
    risk_level: string;
    user_ml_per_ha: number;
    benchmark_mean: number | null;
    benchmark_std: number | null;
    sample_size: number | null;
    lls_region: string | null;
    valley_name: string | null;
  };

  optimization_mode: string;
  target_savings_ml: number | null;
  budget_aud: number | null;

  selected_strategies: BackendStrategy[];

  total_annual_cost_aud: number;
  total_estimated_savings_ml: number;
  cost_per_ml_saved_aud: number | null;

  projected_water_use_ml_per_ha: number;
  projected_z_score: number | null;
  projected_risk_level: string;

  excluded_strategies_note: string;

  projection?: WaterProjection | null;
}

export interface ProjectionTimelinePoint {
  month: number;
  projected_water_intensity_ml_per_ha: number;
  cumulative_water_saved_ml: number;
  cumulative_water_saved_ml_per_ha: number;
}

export interface WaterProjection {
  current_water_intensity_ml_per_ha: number;
  projected_water_intensity_ml_per_ha: number;
  annual_water_saved_ml: number;
  annual_water_saved_ml_per_ha: number;
  reduction_percent: number;
  annual_cost_aud: number;
  cost_per_ml_saved_aud: number | null;
  timeline: ProjectionTimelinePoint[];
}

/* =========================================================
   FRONTEND SUGGESTION TYPE
   ========================================================= */

export interface Suggestion {
  id: string;
  title: string;
  category: string;

  shortDescription: string;
  explanation: string;
  actions: string[];

  impact: "low" | "medium" | "high";
  difficulty: "easy" | "moderate" | "advanced";

  estimatedWaterReductionPct?: number | null;
  annualCostAud?: number | null;
  estimatedSavingsMl?: number | null;
  confidence?: string | null;
  source?: string | null;
}

export interface BusinessData {
  location: {
    postcode: string | number;
    suburb?: string | null;
    state?: string | null;
  };
  cropCategory: string;
  waterUsed: number;
  landArea: number;
  currentIrrigationMethod?: string;
  budgetAud?: number | null;
}

export const DEFAULT_BUDGET_AUD = 15000;
const BUDGET_MIN = 0;
const BUDGET_MAX = 100000;
const BUDGET_STEP = 1000;
const BUDGET_DEBOUNCE_MS = 400;

interface RecommendationSummary {
  strategyCount: number;
  totalAnnualCostAud: number;
  totalEstimatedSavingsMl: number;
}

interface SuggestionsProps {
  suggestions?: Suggestion[];
  currentWaterUse: number;
  businessData?: BusinessData | null;
  onRecommendationResult?: (
    data: RecommendationResponse
  ) => void;
  onBack?: () => void;
}

function formatAud(value: number) {
  return `$${Math.round(value).toLocaleString("en-AU")}`;
}

function formatMl(value: number) {
  return value.toLocaleString("en-AU", {
    maximumFractionDigits: 2,
  });
}

function whyThisMayHelp(category: string) {
  const key = category.toLowerCase();

  if (key.includes("maintenance")) {
    return "This strategy may help reduce avoidable water losses by improving irrigation system efficiency and identifying leaks or uneven delivery.";
  }

  if (key.includes("monitor")) {
    return "This strategy may help match irrigation more closely to crop need by using better information to time watering.";
  }

  if (key.includes("automat")) {
    return "This strategy may help reduce over-application by improving control of when water is delivered.";
  }

  if (key.includes("agronom")) {
    return "This strategy may help the farm use applied water more effectively through agronomic practice rather than extra water input.";
  }

  return "This strategy may help the farm use water more efficiently by changing how irrigation is managed or delivered.";
}

/* =========================================================
   BACKEND -> FRONTEND CONVERTER
   ========================================================= */

export function strategyToSuggestion(
  strategy: BackendStrategy
): Suggestion {
  const savingPct =
    (strategy.savings_pct_applied ?? 0) * 100;

  /*
    These are currently frontend display categories.

    They do NOT affect the backend optimiser.
  */
  let impact: Suggestion["impact"] = "low";

  if (savingPct >= 15) {
    impact = "high";
  } else if (savingPct >= 7) {
    impact = "medium";
  }

  const disruption =
    strategy.implementation_disruption
      ?.toLowerCase() ?? "";

  let difficulty: Suggestion["difficulty"] =
    "moderate";

  if (
    disruption.includes("low") ||
    disruption.includes("easy")
  ) {
    difficulty = "easy";
  } else if (
    disruption.includes("high") ||
    disruption.includes("advanced")
  ) {
    difficulty = "advanced";
  }

  return {
    id: strategy.id,
    title: strategy.name,
    category: strategy.category,

    shortDescription:
      `Estimated to save ${strategy.estimated_savings_ml.toFixed(
        2
      )} ML of water annually.`,

    explanation: whyThisMayHelp(strategy.category),

    actions: [
      `Review ${strategy.name}`,
      `Consider the estimated annual cost of ${formatAud(
        strategy.annual_cost_aud
      )}`,
      `Review the supporting source before implementation`,
    ],

    impact,
    difficulty,

    estimatedWaterReductionPct: savingPct,
    annualCostAud: strategy.annual_cost_aud,
    estimatedSavingsMl: strategy.estimated_savings_ml,
    confidence: strategy.confidence,
    source: strategy.source,
  };
}

/* =========================================================
   IMPACT COLOURS
   ========================================================= */

const impactColour = {
  high: "#65c995",
  medium: "#8997c1",
  low: "#f19a93",
};

/* =========================================================
   COMPONENT
   ========================================================= */

export default function Suggestions({
  suggestions = [],
  currentWaterUse,
  businessData = null,
  onRecommendationResult,
  onBack,
}: SuggestionsProps) {
  const [rotation, setRotation] =
    useState(0);

  const [isDragging, setIsDragging] =
    useState(false);

  const [items, setItems] =
    useState<Suggestion[]>(suggestions);

  const [budgetAud, setBudgetAud] =
    useState(
      businessData?.budgetAud ??
        DEFAULT_BUDGET_AUD
    );

  const [isUpdating, setIsUpdating] =
    useState(false);

  const [updateError, setUpdateError] =
    useState<string | null>(null);

  const [summary, setSummary] =
    useState<RecommendationSummary | null>(
      null
    );

  const dragStartX = useRef(0);
  const dragStartRotation = useRef(0);
  const skipInitialFetch = useRef(true);

  useEffect(() => {
    setItems(suggestions);
  }, [suggestions]);

  useEffect(() => {
    setRotation(0);
  }, [items]);

  useEffect(() => {
    if (!businessData) {
      return;
    }

    if (skipInitialFetch.current) {
      skipInitialFetch.current = false;
      return;
    }

    const controller = new AbortController();
    let cancelled = false;

    const timeout = window.setTimeout(async () => {
      setIsUpdating(true);
      setUpdateError(null);

      try {
        const response = await fetch(
          "/api/recommend-strategies",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            signal: controller.signal,
            body: JSON.stringify({
              location: {
                postcode: businessData.location.postcode,
                suburb: businessData.location.suburb,
                state: businessData.location.state,
              },
              cropCategory: businessData.cropCategory,
              waterUsed: businessData.waterUsed,
              landArea: businessData.landArea,
              currentIrrigationMethod:
                businessData.currentIrrigationMethod ??
                "unknown",
              budgetAud,
            }),
          }
        );

        const text = await response.text();

        if (!response.ok) {
          throw new Error(
            `${response.status} ${response.statusText} — ${text}`
          );
        }

        const data: RecommendationResponse =
          JSON.parse(text);

        if (cancelled) {
          return;
        }

        setItems(
          data.selected_strategies.map(
            strategyToSuggestion
          )
        );

        onRecommendationResult?.(data);

        setSummary({
          strategyCount:
            data.selected_strategies.length,
          totalAnnualCostAud:
            data.total_annual_cost_aud,
          totalEstimatedSavingsMl:
            data.total_estimated_savings_ml,
        });
      } catch (error) {
        if (
          cancelled ||
          (error instanceof DOMException &&
            error.name === "AbortError")
        ) {
          return;
        }

        console.error(
          "Unable to update recommendations:",
          error
        );
        setUpdateError(
          "Unable to update recommendations. Please try again."
        );
      } finally {
        if (!cancelled) {
          setIsUpdating(false);
        }
      }
    }, BUDGET_DEBOUNCE_MS);

    return () => {
      cancelled = true;
      controller.abort();
      window.clearTimeout(timeout);
    };
  }, [budgetAud, businessData]);

  const cardCount = items.length;

  const anglePerCard =
    cardCount > 0
      ? 360 / cardCount
      : 0;

  /* =======================================================
     ACTIVE CARD
     ======================================================= */

  const activeIndex = useMemo(() => {
    if (!cardCount) {
      return 0;
    }

    const normalised =
      ((-rotation % 360) + 360) % 360;

    return (
      Math.round(
        normalised / anglePerCard
      ) % cardCount
    );
  }, [
    rotation,
    anglePerCard,
    cardCount,
  ]);

  const selected =
    items[activeIndex];

  /* =======================================================
     ROTATION
     ======================================================= */

  const rotateTo = (
    index: number
  ) => {
    if (!cardCount) {
      return;
    }

    setRotation(
      -index * anglePerCard
    );
  };

  const rotateNext = () => {
    if (!cardCount) {
      return;
    }

    rotateTo(
      (activeIndex + 1) %
        cardCount
    );
  };

  const rotatePrevious = () => {
    if (!cardCount) {
      return;
    }

    rotateTo(
      (activeIndex -
        1 +
        cardCount) %
        cardCount
    );
  };

  /* =======================================================
     DRAGGING
     ======================================================= */

  const handlePointerDown = (
    event: React.PointerEvent<HTMLDivElement>
  ) => {
    if (!cardCount) {
      return;
    }

    dragStartX.current =
      event.clientX;

    dragStartRotation.current =
      rotation;

    setIsDragging(true);

    event.currentTarget.setPointerCapture(
      event.pointerId
    );
  };

  const handlePointerMove = (
    event: React.PointerEvent<HTMLDivElement>
  ) => {
    if (!isDragging) {
      return;
    }

    const difference =
      event.clientX -
      dragStartX.current;

    setRotation(
      dragStartRotation.current +
        difference * 0.25
    );
  };

  const handlePointerUp = () => {
    if (
      !isDragging ||
      !cardCount
    ) {
      return;
    }

    setIsDragging(false);

    const nearest =
      Math.round(
        rotation / anglePerCard
      ) * anglePerCard;

    setRotation(nearest);
  };

  /* =======================================================
     KEYBOARD
     ======================================================= */

  useEffect(() => {
    const handleKeyboard = (
      event: KeyboardEvent
    ) => {
      if (event.key === "ArrowLeft") {
        rotatePrevious();
      }

      if (event.key === "ArrowRight") {
        rotateNext();
      }
    };

    window.addEventListener(
      "keydown",
      handleKeyboard
    );

    return () => {
      window.removeEventListener(
        "keydown",
        handleKeyboard
      );
    };
  });

  const budgetControl = (
    <div className="budget-control">
      <div className="budget-control-header">
        <label htmlFor="annual-budget">
          Annual budget
        </label>
        <strong>{formatAud(budgetAud)}</strong>
      </div>

      <input
        id="annual-budget"
        className="budget-slider"
        type="range"
        min={BUDGET_MIN}
        max={BUDGET_MAX}
        step={BUDGET_STEP}
        value={budgetAud}
        onChange={(event) => {
          setBudgetAud(Number(event.target.value));
        }}
      />

      <div className="budget-control-range">
        <span>{formatAud(BUDGET_MIN)}</span>
        <span>{formatAud(BUDGET_MAX)}</span>
      </div>

      {summary && (
        <p className="budget-summary">
          Selected budget: {formatAud(budgetAud)}
          {" · "}
          Recommended strategies: {summary.strategyCount}
          {" · "}
          Estimated annual cost:{" "}
          {formatAud(summary.totalAnnualCostAud)}
          {" · "}
          Estimated water saving:{" "}
          {summary.totalEstimatedSavingsMl.toLocaleString(
            "en-AU"
          )}{" "}
          ML
        </p>
      )}

      {isUpdating && (
        <p className="budget-status">
          Updating recommendations…
        </p>
      )}

      {updateError && (
        <p className="budget-error">
          {updateError}
        </p>
      )}
    </div>
  );

  const pageIntro = (
    <div className="relative z-20 mx-auto flex w-full max-w-[1320px] items-start justify-between gap-6 pt-5">

      <div className="suggestions-intro glass-intro relative z-30">

        {onBack && (
          <button
            type="button"
            onClick={onBack}
            className="mb-7 text-sm font-medium text-[#72789c] transition hover:text-[#555b78]"
          >
            ← Back to comparison
          </button>
        )}

        <p className="mb-3 text-xs font-bold tracking-[0.18em] text-[#7f78db]">
          RECOMMENDED ACTIONS
        </p>

        <h1 className="text-4xl font-medium leading-[1.04] tracking-[-0.045em] md:text-5xl">
          Explore your
          <br />
          opportunities
        </h1>

        <p className="mt-4 max-w-[330px] text-[15px] leading-6 text-[#7d829a]">
          Drag the circle to explore
          actions. Click any action to
          view its details and potential
          impact.
        </p>

        {budgetControl}

      </div>

      <div className="mt-20 hidden items-center gap-5 text-xs md:flex">

        <div className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-[#65c995]" />
          <span>
            Higher potential impact
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-[#8997c1]" />
          <span>
            Medium potential impact
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className="h-2.5 w-2.5 rounded-full bg-[#f19a93]" />
          <span>
            Lower potential impact
          </span>
        </div>

      </div>
    </div>
  );

  if (!selected) {
    return (
      <section className="relative w-full overflow-x-hidden px-6 pb-10 text-[#555b78]">
        {pageIntro}

        <div className="mx-auto mt-10 w-full max-w-[1180px] rounded-[26px] border border-[#dcdde8] bg-white/75 p-8 text-center backdrop-blur-xl">
          <p className="text-xs font-bold tracking-[0.18em] text-[#7f78db]">
            RECOMMENDED ACTIONS
          </p>

          <h2 className="mt-3 text-2xl font-medium">
            No recommendations available
          </h2>

          <p className="mt-2 text-sm text-[#7d829a]">
            No strategies were found
            within the selected budget.
          </p>
        </div>
      </section>
    );
  }

  const reduction =
    selected.estimatedWaterReductionPct ??
    0;

  const potentialWaterUse =
    currentWaterUse *
    (1 - reduction / 100);

  return (
    <section className="relative w-full overflow-x-hidden px-6 pb-10 text-[#555b78]">

      {pageIntro}

      {/* ================================================ */}
      {/* 3D RECOMMENDATION WHEEL */}
      {/* ================================================ */}

      <div
        className={`suggestion-stage ${
          isDragging
            ? "is-dragging"
            : ""
        }${isUpdating ? " is-updating" : ""}`}
        onPointerDown={
          handlePointerDown
        }
        onPointerMove={
          handlePointerMove
        }
        onPointerUp={
          handlePointerUp
        }
        onPointerCancel={
          handlePointerUp
        }
      >

        {/* FLOOR */}

        <div className="suggestion-floor">

          <div className="floor-ring ring-1" />
          <div className="floor-ring ring-2" />
          <div className="floor-ring ring-3" />
          <div className="floor-ring ring-4" />

          {Array.from({
            length: 18,
          }).map((_, index) => (
            <div
              key={index}
              className="floor-spoke"
              style={{
                transform: `rotate(${
                  index * 20
                }deg)`,
              }}
            />
          ))}

        </div>

        {/* ACTUAL CAROUSEL */}

        <div className="wheel-camera">

          <div
            className="recommendation-wheel"
            style={{
              transform:
                `rotateY(${rotation}deg)`,

              transition:
                isDragging
                  ? "none"
                  : undefined,
            }}
          >

            {items.map(
              (
                suggestion,
                index
              ) => {
                const angle =
                  index *
                  anglePerCard;

                const isActive =
                  index ===
                  activeIndex;

                return (
                  <button
                    type="button"
                    key={
                      suggestion.id
                    }
                    className={`recommendation-orbit-card ${
                      isActive
                        ? "active"
                        : ""
                    }`}
                    style={{
                      transform: `
                        rotateY(${angle}deg)
                        translateZ(390px)
                      `,
                    }}
                    onClick={(
                      event
                    ) => {
                      event.stopPropagation();

                      rotateTo(
                        index
                      );
                    }}
                  >

                    <div className="flex h-full flex-col">

                      <div className="flex items-center justify-between">

                        <span className="rounded-full bg-[#f3f2fb] px-2.5 py-1 text-[9px] font-bold uppercase tracking-[0.12em] text-[#7774c8]">
                          {
                            suggestion.category
                          }
                        </span>

                        <span
                          className="h-2 w-2 rounded-full"
                          style={{
                            background:
                              impactColour[
                                suggestion
                                  .impact
                              ],
                          }}
                        />

                      </div>

                      <h3 className="mt-2 text-left text-xl font-medium leading-tight tracking-[-0.035em]">
                        {
                          suggestion.title
                        }
                      </h3>

                      <p className="mt-2 text-left text-xs leading-5 text-[#85899e]">
                        {
                          suggestion.shortDescription
                        }
                      </p>

                      {suggestion.estimatedWaterReductionPct !=
                        null && (
                        <div className="mt-auto rounded-xl bg-white/60 px-3 py-2 text-left">

                          <strong className="block text-lg font-medium text-[#45a976]">
                            ↑{" "}
                            {
                              suggestion.estimatedWaterReductionPct
                            }
                            %
                          </strong>

                          <span className="text-[10px] text-[#75a68a]">
                            Potential water
                            saving
                          </span>

                        </div>
                      )}

                    </div>

                  </button>
                );
              }
            )}

          </div>
        </div>

        {/* LEFT CONTROL */}

        <button
          type="button"
          className="wheel-arrow left"
          onClick={(event) => {
            event.stopPropagation();
            rotatePrevious();
          }}
          aria-label="Previous recommendation"
        >
          ←
        </button>

        {/* RIGHT CONTROL */}

        <button
          type="button"
          className="wheel-arrow right"
          onClick={(event) => {
            event.stopPropagation();
            rotateNext();
          }}
          aria-label="Next recommendation"
        >
          →
        </button>

      </div>

      {/* ================================================ */}
      {/* ACTIVE SUGGESTION DETAILS */}
      {/* ================================================ */}

      <div className="selected-strategy-panel mx-auto mt-8 w-full max-w-[1180px]">

        <div className="selected-strategy-main">

          <div className="selected-strategy-copy">

            <span className="rounded-lg bg-[#eeecff] px-2 py-1 text-[10px] font-bold uppercase tracking-[0.12em] text-[#736bd8]">
              {selected.category}
            </span>

            <h2 className="selected-strategy-title">
              {selected.title}
            </h2>

            <p className="why-help-kicker why-help-heading">
              WHY THIS MAY HELP
            </p>

            <p className="why-help-copy">
              {selected.explanation}
            </p>

          </div>

          <div className="selected-strategy-metrics">

            <p className="why-help-kicker">
              POTENTIAL IMPACT
            </p>

            <div className="selected-strategy-impact">

              <div>
                <strong className="saving-value">
                  {selected.estimatedWaterReductionPct !=
                  null
                    ? `${selected.estimatedWaterReductionPct}%`
                    : "—"}
                </strong>
                <span>Water saving</span>
              </div>

              <div>
                <strong>
                  {currentWaterUse.toFixed(2)}{" "}
                  <small>ML/ha</small>
                </strong>
                <span>Current use</span>
              </div>

              <span className="impact-arrow">→</span>

              <div>
                <strong>
                  {potentialWaterUse.toFixed(2)}{" "}
                  <small>ML/ha</small>
                </strong>
                <span>Potential use</span>
              </div>

            </div>

            <div className="why-help-stats">

              <div className="why-help-stat">
                <span>Estimated annual cost</span>
                <strong>
                  {selected.annualCostAud != null
                    ? formatAud(selected.annualCostAud)
                    : "—"}
                </strong>
              </div>

              <div className="why-help-stat saving">
                <span>Estimated water saving</span>
                <strong>
                  {selected.estimatedSavingsMl != null
                    ? `${formatMl(selected.estimatedSavingsMl)} ML`
                    : "—"}
                </strong>
              </div>

            </div>

          </div>

        </div>

        <div className="why-help-meta">
          <p>
            <span>Confidence</span>
            <strong className="capitalize">
              {selected.confidence || "Not specified"}
            </strong>
          </p>

          {selected.source && (
            <p>
              <span>Source</span>
              <strong className="why-help-source">
                {selected.source}
              </strong>
            </p>
          )}
        </div>

      </div>

    </section>
  );
}