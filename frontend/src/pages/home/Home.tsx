import { useEffect, useRef, useState } from "react";
import "./Home.css";
import Scenarios, {
  type BenchmarkResult,
} from "../scenarios/Scenarios";

interface LocationEntry {
  postcode: string | number;
  suburb: string;
  state: string;
  region_id: string;
  VALLEY_NAME: string;
}

interface BusinessData {
  location: LocationEntry;
  cropCategory: string;
  waterUsed: number;
  landArea: number;
}

export default function Home() {
  const [step, setStep] = useState(1);

  const [location, setLocation] = useState("");
  const [matchedLocation, setMatchedLocation] =
    useState<LocationEntry | null>(null);

  const [cropCategory, setCropCategory] = useState("");
  const [waterUsed, setWaterUsed] = useState("");
  const [landArea, setLandArea] = useState("");

  const [locationError, setLocationError] = useState("");
  const [isAnalysing, setIsAnalysing] = useState(false);

  const [benchmark, setBenchmark] =
  useState<BenchmarkResult | null>(null);

  const [isRevealed, setIsRevealed] = useState(false);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const cardRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const node = containerRef.current;

    if (!node) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsRevealed(true);
          observer.disconnect();
        }
      },
      { threshold: 0.25 }
    );

    observer.observe(node);

    return () => observer.disconnect();
  }, []);
  const [summary, setSummary] = useState<string | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(false);

  const cropOptions = [
    "Grains & Oilseeds",
    "Pasture & Livestock Feed",
    "Vegetables",
    "Grapes & Vineyards",
    "Fruit & Nuts",
    "Cotton",
    "Rice",
    "Other",
  ];

  const nextStep = () => {
    setStep((current) => Math.min(current + 1, 4));
  };

  const previousStep = () => {
    setStep((current) => Math.max(current - 1, 1));
  };

  // Tracks the pointer position over the glass card so the liquid-glass
  // glow (driven by the --mx / --my CSS vars in Home.css) can follow it.
  const handleCardMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 100;
    const y = ((e.clientY - rect.top) / rect.height) * 100;

    e.currentTarget.style.setProperty("--mx", `${x}%`);
    e.currentTarget.style.setProperty("--my", `${y}%`);
  };

  const submitLocation = async () => {
    try {
      setLocationError("");

      const response = await fetch("/data/postcode_map.json");

      if (!response.ok) {
        console.error(
          "Failed to load postcode_map.json:",
          response.status,
          response.statusText
        );

        setLocationError(
          "Location data could not be loaded. Please try again."
        );

        return;
      }

      const postcodeMap: LocationEntry[] = await response.json();

      const userInput = location.trim().toLowerCase();

      const match = postcodeMap.find((entry) => {
        const postcode = String(entry.postcode)
          .trim()
          .toLowerCase();

        const suburb = String(entry.suburb)
          .trim()
          .toLowerCase();

        return postcode === userInput || suburb === userInput;
      });

      if (!match) {
        console.log("No location found for:", location);

        setLocationError(
          "We couldn't find that suburb or postcode. Try another NSW suburb or postcode."
        );

        return;
      }

      setMatchedLocation(match);

      console.log("===== LOCATION MATCH =====");
      console.log("User entered:", location);
      console.log("Full dictionary entry:", match);
      console.log("Postcode:", match.postcode);
      console.log("Suburb:", match.suburb);
      console.log("State:", match.state);
      console.log("Region ID:", match.region_id);
      console.log("Valley:", match.VALLEY_NAME);
      console.log("==========================");

      setStep(2);
    } catch (error) {
      console.error("Location lookup failed:", error);

      setLocationError(
        "Location data could not be loaded. Please try again."
      );
    }
  };

    const handleAnalyse = async () => {
        console.log("ANALYSE BUTTON CLICKED");

        if (!matchedLocation) {
            console.error("No matched location available.");
            return;
        }

        const businessData = {
            location: matchedLocation,
            cropCategory,
            waterUsed: Number(waterUsed),
            landArea: Number(landArea),
        };

        console.log("SENDING:", businessData);

        try {
            setIsAnalysing(true);

            const response = await fetch("/api/analyse", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(businessData),
            });

            console.log("RESPONSE STATUS:", response.status);

            const text = await response.text();

            console.log("RAW BACKEND RESPONSE:", text);

            if (!response.ok) {
            console.error("Analysis failed:", response.status, text);
            return;
            }

            const data = text ? JSON.parse(text) : null;

            console.log("BACKEND RESPONSE:", data);

            setBenchmark(data.benchmark);

            // Plain-English summary — non-blocking. The stats already render;
            // this fills in when it's ready, and it's fine if it never does.
            setSummary(null);
            setSummaryLoading(true);
            fetch("/api/analyse/explain", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(businessData),
            })
                .then((res) => (res.ok ? res.json() : null))
                .then((payload) => setSummary(payload?.explanation ?? null))
                .catch(() => setSummary(null))
                .finally(() => setSummaryLoading(false));
        } catch (error) {
            console.error("FETCH FAILED:", error);
        } finally {
            setIsAnalysing(false);
        }
    };

    if (benchmark) {
        return (
            <Scenarios
                benchmark={benchmark}
                summary={summary}
                summaryLoading={summaryLoading}
            />
        );
    }

  return (
    <section id="home" className="home">
      <div
        ref={containerRef}
        className={`question-container ${isRevealed ? "revealed" : ""}`}
      >

        {/* Progress */}
        <div className="question-progress">
          <span>0{step}</span>

          <div className="progress-line">
            <div
              className="progress-fill"
              style={{
                width: `${(step / 4) * 100}%`,
              }}
            />
          </div>

          <span>04</span>
        </div>

        {/* GLASS CARD — holds the active question */}
        <div
          className="glass-card"
          ref={cardRef}
          onMouseMove={handleCardMouseMove}
        >
          {/* STEP 1 — LOCATION */}
          {step === 1 && (
            <div className="question-page">
              <p className="question-label">
                YOUR BUSINESS
              </p>

              <h2>
                Where are you located?
              </h2>

              <p className="question-description">
                We'll use your location to understand
                the water conditions affecting your region.
              </p>

              <input
                className="location-input"
                type="text"
                placeholder="e.g. Griffith or 2680"
                value={location}
                onChange={(e) => {
                  setLocation(e.target.value);
                  setLocationError("");
                  setMatchedLocation(null);
                }}
                onKeyDown={(e) => {
                  if (
                    e.key === "Enter" &&
                    location.trim()
                  ) {
                    submitLocation();
                  }
                }}
              />

              {locationError && (
                <p className="location-error">
                  {locationError}
                </p>
              )}

              <button
                className="continue-button"
                onClick={submitLocation}
                disabled={!location.trim()}
              >
                Continue →
              </button>
            </div>
          )}

          {/* STEP 2 — CROP */}
          {step === 2 && (
            <div className="question-page">
              <p className="question-label">
                YOUR PRODUCTION
              </p>

              <h2>
                What best describes your crops?
              </h2>

              <p className="question-description">
                This helps us compare your water use
                with a more relevant agricultural benchmark.
              </p>

              <div className="option-grid">
                {cropOptions.map((crop) => (
                  <button
                    key={crop}
                    type="button"
                    className={
                      cropCategory === crop
                        ? "option-card selected"
                        : "option-card"
                    }
                    onClick={() => {
                      setCropCategory(crop);
                    }}
                  >
                    {crop}
                  </button>
                ))}
              </div>

              <button
                className="continue-button"
                onClick={nextStep}
                disabled={!cropCategory}
              >
                Continue →
              </button>
            </div>
          )}

          {/* STEP 3 — WATER */}
          {step === 3 && (
            <div className="question-page">
              <p className="question-label">
                WATER USE
              </p>

              <h2>
                How much water did you use last year?
              </h2>

              <p className="question-description">
                Enter your total annual water use
                in megalitres.
              </p>

              <div className="large-input">
                <input
                  type="number"
                  min="0"
                  placeholder="1200"
                  value={waterUsed}
                  onChange={(e) => {
                    setWaterUsed(e.target.value);
                  }}
                />

                <span>ML</span>
              </div>

              <button
                className="continue-button"
                onClick={nextStep}
                disabled={
                  !waterUsed ||
                  Number(waterUsed) <= 0
                }
              >
                Continue →
              </button>
            </div>
          )}

          {/* STEP 4 — LAND */}
          {step === 4 && (
            <div className="question-page">
              <p className="question-label">
                LAND
              </p>

              <h2>
                How much irrigated land do you operate?
              </h2>

              <p className="question-description">
                We'll use this to calculate your
                water application rate.
              </p>

              <div className="large-input">
                <input
                  type="number"
                  min="0"
                  placeholder="250"
                  value={landArea}
                  onChange={(e) => {
                    setLandArea(e.target.value);
                  }}
                />

                <span>hectares</span>
              </div>

              <button
                  className="continue-button analyse"
                  onClick={handleAnalyse}
                  >
                  Analyse My Water Performance →
              </button>
            </div>
          )}
        </div>

        {/* BACK */}
        {step > 1 && (
          <button
            className="back-button"
            onClick={previousStep}
          >
            ← Back
          </button>
        )}
      </div>
    </section>
  );
}
