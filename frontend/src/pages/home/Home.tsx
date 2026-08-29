import { useState } from "react";
import "./Home.css";

export default function Home() {
  const [step, setStep] = useState(1);

  const [location, setLocation] = useState("");
  const [cropCategory, setCropCategory] = useState("");
  const [waterUsed, setWaterUsed] = useState("");
  const [landArea, setLandArea] = useState("");
  const [waterSource, setWaterSource] = useState("");

  const nextStep = () => {
    setStep((current) => Math.min(current + 1, 4));
  };

  const previousStep = () => {
    setStep((current) => Math.max(current - 1, 1));
  };

  const handleAnalyse = () => {
    const businessData = {
      location,
      cropCategory,
      waterUsed,
      landArea,
    };

    console.log(businessData);

    // Later:
    // send businessData to backend
    // then show/scroll to results
  };

  return (
    <section id="home" className="home">
      <div className="question-container">

        {/* Progress */}
        <div className="question-progress">
          <span>0{step}</span>
          <div className="progress-line">
            <div
              className="progress-fill"
              style={{ width: `${(step / 4) * 100}%` }}
            />
          </div>
          <span>04</span>
        </div>

        {/* STEP 1 */}
        {step === 1 && (
          <div className="question-page">
            <p className="question-label">YOUR BUSINESS</p>

            <h2>Where are you located?</h2>

            <p className="question-description">
              We'll use your location to understand the water conditions
              affecting your region.
            </p>

            <select
              value={location}
              onChange={(e) => setLocation(e.target.value)}
            >
              <option value="">Select your location</option>
              <option value="griffith">Griffith</option>
              <option value="moree-plains">Moree Plains</option>
              <option value="orange">Orange</option>
              <option value="dubbo">Dubbo</option>
              <option value="wagga-wagga">Wagga Wagga</option>
            </select>

            <button
              className="continue-button"
              onClick={nextStep}
              disabled={!location}
            >
              Continue →
            </button>
          </div>
        )}

        {/* STEP 2 */}
        {step === 2 && (
          <div className="question-page">
            <p className="question-label">YOUR PRODUCTION</p>

            <h2>What best describes your crops?</h2>

            <p className="question-description">
              This helps us compare your water use with a more relevant
              agricultural benchmark.
            </p>

            <div className="option-grid">
              {[
                "Grains & Oilseeds",
                "Pasture & Livestock Feed",
                "Vegetables",
                "Grapes & Vineyards",
                "Fruit & Nuts",
                "Cotton",
                "Rice",
                "Other",
              ].map((crop) => (
                <button
                  key={crop}
                  className={
                    cropCategory === crop
                      ? "option-card selected"
                      : "option-card"
                  }
                  onClick={() => setCropCategory(crop)}
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

        {/* STEP 3 */}
        {step === 3 && (
          <div className="question-page">
            <p className="question-label">WATER USE</p>

            <h2>How much water did you use last year?</h2>

            <p className="question-description">
              Enter your total annual water use in megalitres.
            </p>

            <div className="large-input">
              <input
                type="number"
                min="0"
                placeholder="1,200"
                value={waterUsed}
                onChange={(e) => setWaterUsed(e.target.value)}
              />
              <span>ML</span>
            </div>

            <button
              className="continue-button"
              onClick={nextStep}
              disabled={!waterUsed}
            >
              Continue →
            </button>
          </div>
        )}

        {/* STEP 4 */}
        {step === 4 && (
          <div className="question-page">
            <p className="question-label">LAND</p>

            <h2>How much irrigated land do you operate?</h2>

            <p className="question-description">
              We'll use this to calculate your water application rate.
            </p>

            <div className="large-input">
              <input
                type="number"
                min="0"
                placeholder="250"
                value={landArea}
                onChange={(e) => setLandArea(e.target.value)}
              />
              <span>hectares</span>
            </div>

            <button
              className="continue-button"
              onClick={nextStep}
              disabled={!landArea}
            >
              Continue →
            </button>
          </div>
        )}


        {/* Back */}
        {step > 1 && (
          <button className="back-button" onClick={previousStep}>
            ← Back
          </button>
        )}
      </div>
    </section>
  );
}