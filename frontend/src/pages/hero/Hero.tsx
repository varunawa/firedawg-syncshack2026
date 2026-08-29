import { useEffect, useRef, useState } from "react";
import "./Hero.css";
import PixiStage from "../../components/PixiStage";

export default function Hero() {
  const [isLeaving, setIsLeaving] = useState(false);
  const wrapperRef = useRef<HTMLDivElement | null>(null);
  const heroRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    let ticking = false;

    const updateParallax = () => {
      ticking = false;

      const wrapper = wrapperRef.current;
      const hero = heroRef.current;

      if (!wrapper || !hero) return;

      const scrollDistance = wrapper.offsetHeight - window.innerHeight;
      const scrolled = -wrapper.getBoundingClientRect().top;

      const progress =
        scrollDistance > 0
          ? Math.min(Math.max(scrolled / scrollDistance, 0), 1)
          : 0;

      hero.style.setProperty("--p", progress.toString());
    };

    const onScroll = () => {
      if (!ticking) {
        ticking = true;
        requestAnimationFrame(updateParallax);
      }
    };

    updateParallax();

    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);

    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
    };
  }, []);

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
    <div className="hero-wrapper" ref={wrapperRef}>
      <section
        ref={heroRef}
        className={`hero ${isLeaving ? "hero-leaving" : ""}`}
      >
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

        <div className="hero-bottom">Scroll to begin</div>

        <div className="hero-transition" />
      </section>
    </div>
  );
}