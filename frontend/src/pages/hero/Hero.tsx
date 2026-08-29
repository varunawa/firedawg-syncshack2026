import { useState } from "react";
import "./Hero.css";
import PixiStage from "../../components/PixiStage";

export default function Hero() {
  const [isLeaving, setIsLeaving] = useState(false);

  const scrollToHome = () => {
    setIsLeaving(true);

    setTimeout(() => {
      document
        .getElementById("home")
        ?.scrollIntoView({
          behavior: "smooth",
        });

      setTimeout(() => {
        setIsLeaving(false);
      }, 800);
    }, 450);
  };

  return (
    <section className={`hero ${isLeaving ? "hero-leaving" : ""}`}>
      <div className="hero-background" />
      <div className="hero-overlay" />

      <PixiStage />

      <div className="hero-content">
        <p className="hero-eyebrow">
          WATER INTELLIGENCE FOR NSW AGRICULTURE
        </p>

        <h1>H2.OS</h1>

        <h2>
          Understand your water.
          <br />
          Prepare for what&apos;s next.
        </h2>

        <p className="hero-description">
          Benchmark your water use, understand regional water conditions,
          and plan for a more resilient future.
        </p>

        <button
          className="hero-button"
          onClick={scrollToHome}
          disabled={isLeaving}
        >
          <span className="button-text">
            Analyse Your Business
          </span>

          <span className="button-arrow">→</span>
        </button>
      </div>

      <div className="hero-transition" />
    </section>
  );
}