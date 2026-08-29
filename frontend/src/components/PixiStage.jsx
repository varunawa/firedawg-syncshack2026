import { useEffect, useRef } from "react";
import { Application, Graphics } from "pixi.js";

/**
 * A PixiJS canvas mounted inside React.
 * PixiJS owns everything inside the <div>; React owns the <div>.
 * Put your game/visualisation code in the async block below.
 */
export default function PixiStage() {
  const hostRef = useRef(null);

  useEffect(() => {
    const app = new Application();
    let disposed = false;

    (async () => {
      await app.init({ background: "#0f172a", resizeTo: hostRef.current });
      if (disposed) return;
      hostRef.current.appendChild(app.canvas);

      const ball = new Graphics().circle(0, 0, 20).fill("#38bdf8");
      ball.position.set(60, 60);
      app.stage.addChild(ball);

      let vx = 3.5;
      let vy = 2.5;
      app.ticker.add(() => {
        ball.x += vx;
        ball.y += vy;
        if (ball.x < 20 || ball.x > app.screen.width - 20) vx = -vx;
        if (ball.y < 20 || ball.y > app.screen.height - 20) vy = -vy;
      });
    })();

    return () => {
      disposed = true;
      app.destroy(true, { children: true });
    };
  }, []);

  return (
    <div
      ref={hostRef}
      className="h-72 w-full overflow-hidden rounded-xl border border-slate-200"
    />
  );
}
