import {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import "./Suggestions.css";

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
}

interface SuggestionsProps {
  suggestions?: Suggestion[];
  currentWaterUse: number;
  onBack?: () => void;
}

/*
  TEMPORARY FRONTEND DATA.

  Replace this later with backend suggestions.
*/
const fallbackSuggestions: Suggestion[] = [
  {
    id: "irrigation-scheduling",
    title: "Review irrigation scheduling",
    category: "Irrigation",
    shortDescription:
      "Better align irrigation timing with crop demand and local conditions.",
    explanation:
      "Reviewing irrigation timing may help reduce unnecessary water application by matching watering more closely with crop requirements and current conditions.",
    actions: [
      "Review current irrigation frequency",
      "Consider lower-evaporation watering periods",
      "Use recent weather conditions when planning irrigation",
    ],
    impact: "high",
    difficulty: "moderate",
    estimatedWaterReductionPct: 15,
  },

  {
    id: "soil-moisture",
    title: "Monitor soil moisture",
    category: "Monitoring",
    shortDescription:
      "Use soil moisture data to understand when irrigation is actually needed.",
    explanation:
      "Soil moisture monitoring can provide additional information about water availability in the root zone before irrigation is applied.",
    actions: [
      "Introduce soil moisture sensors",
      "Track moisture between irrigation cycles",
      "Compare readings with irrigation timing",
    ],
    impact: "medium",
    difficulty: "moderate",
    estimatedWaterReductionPct: 10,
  },

  {
    id: "infrastructure",
    title: "Review irrigation infrastructure",
    category: "Infrastructure",
    shortDescription:
      "Check your irrigation system for leaks and uneven water delivery.",
    explanation:
      "Leaks, pressure issues and uneven distribution can increase the amount of water required to achieve the desired crop outcome.",
    actions: [
      "Inspect irrigation lines",
      "Check pressure consistency",
      "Identify damaged equipment",
    ],
    impact: "medium",
    difficulty: "easy",
    estimatedWaterReductionPct: 8,
  },

  {
    id: "weather",
    title: "Use weather-led planning",
    category: "Planning",
    shortDescription:
      "Consider current and expected conditions before applying water.",
    explanation:
      "Weather information provides useful context around rainfall, temperature and evaporation when planning irrigation.",
    actions: [
      "Review rainfall forecasts",
      "Track recent rainfall",
      "Adjust irrigation after significant rainfall",
    ],
    impact: "medium",
    difficulty: "easy",
    estimatedWaterReductionPct: 7,
  },

  {
    id: "application",
    title: "Review application rates",
    category: "Operations",
    shortDescription:
      "Track your water application rate against similar farms.",
    explanation:
      "Regular monitoring can help identify when water application is moving away from typical values for similar agricultural operations.",
    actions: [
      "Track ML/ha across irrigation periods",
      "Compare results with your benchmark",
      "Review major changes in water intensity",
    ],
    impact: "high",
    difficulty: "easy",
    estimatedWaterReductionPct: 12,
  },

  {
    id: "crop-selection",
    title: "Review crop water demand",
    category: "Cropping",
    shortDescription:
      "Understand how crop demand changes across growing conditions.",
    explanation:
      "Reviewing crop water requirements can help provide context for irrigation decisions throughout the growing cycle.",
    actions: [
      "Review crop water requirements",
      "Compare seasonal water demand",
      "Track changes throughout the growing cycle",
    ],
    impact: "low",
    difficulty: "moderate",
    estimatedWaterReductionPct: 5,
  },
];

const impactColour = {
  high: "#65c995",
  medium: "#8997c1",
  low: "#f19a93",
};

export default function Suggestions({
  suggestions = fallbackSuggestions,
  currentWaterUse,
  onBack,
}: SuggestionsProps) {
  const [rotation, setRotation] =
    useState(0);

  const [isDragging, setIsDragging] =
    useState(false);

  const dragStartX = useRef(0);

  const dragStartRotation = useRef(0);

  const cardCount = suggestions.length;

  const anglePerCard =
    cardCount > 0 ? 360 / cardCount : 0;

  /*
    Find which recommendation is currently
    closest to the front of the wheel.
  */
  const activeIndex = useMemo(() => {
    if (!cardCount) return 0;

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
    suggestions[activeIndex];

  const rotateTo = (index: number) => {
    setRotation(-index * anglePerCard);
  };

  const rotateNext = () => {
    rotateTo(
      (activeIndex + 1) %
        suggestions.length
    );
  };

  const rotatePrevious = () => {
    rotateTo(
      (activeIndex -
        1 +
        suggestions.length) %
        suggestions.length
    );
  };

  const handlePointerDown = (
    event: React.PointerEvent<HTMLDivElement>
  ) => {
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
    if (!isDragging) return;

    const difference =
      event.clientX -
      dragStartX.current;

    /*
      Change 0.25 if you want
      faster/slower dragging.
    */
    setRotation(
      dragStartRotation.current +
        difference * 0.25
    );
  };

  const handlePointerUp = () => {
    if (!isDragging) return;

    setIsDragging(false);

    /*
      Snap to nearest card.
    */
    const nearest =
      Math.round(
        rotation / anglePerCard
      ) * anglePerCard;

    setRotation(nearest);
  };

  /*
    Keyboard support.
  */
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

  if (!selected) {
    return null;
  }

  const reduction =
    selected.estimatedWaterReductionPct ??
    0;

  const potentialWaterUse =
    currentWaterUse *
    (1 - reduction / 100);

  return (
    <section className="relative w-full overflow-x-hidden px-6 pb-10 text-[#555b78]">

      {/* ============================= */}
      {/* PAGE INTRO */}
      {/* ============================= */}

      <div className="relative z-20 mx-auto flex w-full max-w-[1320px] items-start justify-between gap-6 pt-5">
        <div className="suggestions-intro glass-intro relative z-30 max-w-[340px]">
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
            Drag the circle to explore actions.
            Click any action to view its details
            and potential impact.
        </p>
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
            <span>Medium potential impact</span>
          </div>

          <div className="flex items-center gap-2">
            <span className="h-2.5 w-2.5 rounded-full bg-[#f19a93]" />

            <span>
              Lower potential impact
            </span>
          </div>
        </div>
      </div>

      {/* ============================= */}
      {/* 3D RECOMMENDATION WHEEL */}
      {/* ============================= */}

      <div
        className={`suggestion-stage ${
          isDragging
            ? "is-dragging"
            : ""
        }`}
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
              transform: `rotateY(${rotation}deg)`,
              transition:
                isDragging
                  ? "none"
                  : undefined,
            }}
          >
            {suggestions.map(
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

                      rotateTo(index);
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

                      <h3 className="mt-5 text-left text-xl font-medium leading-tight tracking-[-0.035em]">
                        {
                          suggestion.title
                        }
                      </h3>

                      <p className="mt-3 flex-1 text-left text-xs leading-5 text-[#85899e]">
                        {
                          suggestion.shortDescription
                        }
                      </p>

                      {suggestion.estimatedWaterReductionPct !=
                        null && (
                        <div className="mt-5 rounded-xl bg-white/60 p-3 text-left">
                          <strong className="block text-lg font-medium text-[#45a976]">
                            ↑{" "}
                            {
                              suggestion.estimatedWaterReductionPct
                            }
                            %
                          </strong>

                          <span className="text-[10px] text-[#75a68a]">
                            Potential
                            water
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


        {/* LEFT / RIGHT CONTROLS */}

        <button
          type="button"
          className="wheel-arrow left"
          onClick={(
            event
          ) => {
            event.stopPropagation();
            rotatePrevious();
          }}
          aria-label="Previous recommendation"
        >
          ←
        </button>

        <button
          type="button"
          className="wheel-arrow right"
          onClick={(
            event
          ) => {
            event.stopPropagation();
            rotateNext();
          }}
          aria-label="Next recommendation"
        >
          →
        </button>

      </div>

      {/* ============================= */}
      {/* ACTIVE SUGGESTION DETAILS */}
      {/* ============================= */}

      <div className="mx-auto 2 grid w-full max-w-[1180px] overflow-hidden rounded-[26px] border border-[#dcdde8] bg-white/75 shadow-[0_18px_55px_rgba(85,91,120,0.08)] backdrop-blur-xl lg:grid-cols-[1.5fr_1.7fr_0.8fr]">

        {/* DESCRIPTION */}

        <div className="border-b border-[#e7e7ee] px-6 py-4 lg:border-b-0 lg:border-r">
          <div className="mb-3 flex items-center gap-2">
            <span className="rounded-lg bg-[#eeecff] px-2 py-1 text-[10px] font-bold uppercase tracking-[0.12em] text-[#736bd8]">
              {selected.category}
            </span>
          </div>

          <h2 className="text-2xl font-medium tracking-[-0.035em]">
            {selected.title}
          </h2>

          <p className="mt-2 text-sm leading-6 text-[#7e839a]">
            {
              selected.shortDescription
            }
          </p>
        </div>

        {/* IMPACT */}

        <div className="border-b border-[#e7e7ee] px-6 py-4 lg:border-b-0 lg:border-r">
          <p className="mb-2 text-[10px] font-bold tracking-[0.16em] text-[#8178db]">
            POTENTIAL IMPACT
          </p>

          <div className="flex items-center justify-between gap-5">
            <div>
              <strong className="text-3xl font-medium text-[#42a976]">
                {selected.estimatedWaterReductionPct !=
                null
                  ? `${selected.estimatedWaterReductionPct}%`
                  : "—"}
              </strong>

              <span className="mt-1 block text-xs text-[#85899d]">
                Water saving
              </span>
            </div>

            <div>
              <strong className="block text-xl font-medium">
                {currentWaterUse.toFixed(
                  2
                )}{" "}
                <small className="text-xs font-normal">
                  ML/ha
                </small>
              </strong>

              <span className="text-xs text-[#9295a5]">
                Current use
              </span>
            </div>

            <span className="text-xl text-[#bbbcca]">
              →
            </span>

            <div>
              <strong className="block text-xl font-medium">
                {potentialWaterUse.toFixed(
                  2
                )}{" "}
                <small className="text-xs font-normal">
                  ML/ha
                </small>
              </strong>

              <span className="text-xs text-[#9295a5]">
                Potential use
              </span>
            </div>
          </div>
        </div>

        {/* DIFFICULTY */}

        <div className="p-7">
          <p className="mb-2 text-[10px] font-bold tracking-[0.16em] text-[#8178db]">
            IMPLEMENTATION
          </p>

          <strong className="capitalize">
            {selected.difficulty}
          </strong>

          <p className="mt-2 text-xs leading-5 text-[#8b8fa3]">
            Review the detailed
            recommendation before
            making operational
            changes.
          </p>
        </div>
      </div>

      {/* ============================= */}
      {/* EXPANDED ACTIONS */}
      {/* ============================= */}

      <div className="mx-auto mt-4 w-full max-w-[1180px] rounded-[24px] border border-[#e1e2ea] bg-white/55 p-7 backdrop-blur-xl">
        <div className="grid gap-10 lg:grid-cols-[1.2fr_1fr]">
          <div>
            <p className="text-[10px] font-bold tracking-[0.16em] text-[#8178db]">
              WHY THIS MAY HELP
            </p>

            <p className="mt-3 max-w-[650px] text-sm leading-6 text-[#777c92]">
              {
                selected.explanation
              }
            </p>
          </div>

          <div>
            <p className="mb-3 text-[10px] font-bold tracking-[0.16em] text-[#8178db]">
              WHAT YOU COULD DO
            </p>

            {selected.actions.map(
              (
                action,
                index
              ) => (
                <div
                  key={action}
                  className="flex gap-4 border-t border-[#e6e6ec] py-3"
                >
                  <span className="text-[10px] font-bold text-[#8d87d8]">
                    {String(
                      index +
                        1
                    ).padStart(
                      2,
                      "0"
                    )}
                  </span>

                  <p className="m-0 text-sm">
                    {action}
                  </p>
                </div>
              )
            )}
          </div>
        </div>
      </div>
    </section>
  );
}