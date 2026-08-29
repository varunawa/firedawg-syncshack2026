import { useEffect, useRef } from "react";
import { Application, Graphics } from "pixi.js";

type PlantPoint = {
  graphic: Graphics;
  baseX: number;
  baseY: number;
  phase: number;
  swayAmount: number;
  baseAlpha: number;
};

export default function PixiStage() {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const container = containerRef.current;

    if (!container) return;

    const pixiContainer: HTMLDivElement = container;

    let cancelled = false;
    let app: Application | null = null;

    async function startPixi() {
      try {
        const pixiApp = new Application();

        await pixiApp.init({
          resizeTo: pixiContainer,
          backgroundAlpha: 0,
          antialias: true,
          autoDensity: true,
          resolution: window.devicePixelRatio || 1,
        });

        if (cancelled) {
          pixiApp.destroy(true, {
            children: true,
          });

          return;
        }

        app = pixiApp;

        pixiContainer.appendChild(pixiApp.canvas);

        const width = pixiApp.screen.width;
        const height = pixiApp.screen.height;

        const centreX = width / 2;

        /*
         * Horizon controls where the fake 3D field begins.
         * Higher number = field starts lower on screen.
         */
        const horizonY = height * 0.56;
        const bottomY = height * 1.04;

        /*
         * Layers
         */
        const gridLayer = new Graphics();

        pixiApp.stage.addChild(gridLayer);

        const plantPoints: PlantPoint[] = [];

        /*
         * =========================
         * SETTINGS
         * =========================
         */

        const CROP_ROWS = 11;
        const PLANTS_PER_ROW = 38;

        /*
         * Distance between crop rows at the bottom.
         */
        const ROW_SPACING = 110;

        /*
         * Number of points that make up each fake plant.
         *
         * More = more "3D scanned" looking,
         * but also more expensive.
         */
        const POINTS_PER_PLANT = 6;

        /*
         * =========================
         * CREATE DIGITAL CROPS
         * =========================
         */

        for (let row = 0; row < CROP_ROWS; row++) {
          const rowOffset =
            (row - (CROP_ROWS - 1) / 2) * ROW_SPACING;

          for (
            let plantIndex = 0;
            plantIndex < PLANTS_PER_ROW;
            plantIndex++
          ) {
            /*
             * 0 = far away
             * 1 = close to camera
             */
            const t =
              plantIndex /
              (PLANTS_PER_ROW - 1);

            /*
             * Non-linear perspective.
             *
             * This squeezes plants together near
             * the horizon and spreads them out
             * near the viewer.
             */
            const perspective =
              Math.pow(t, 1.75);

            const y =
              horizonY +
              perspective *
                (bottomY - horizonY);

            const x =
              centreX +
              rowOffset * perspective;

            /*
             * Plants get taller closer
             * to the viewer.
             */
            const plantHeight =
              5 + perspective * 52;

            /*
             * Plants also get wider near
             * the viewer.
             */
            const plantWidth =
              1 + perspective * 7;

            /*
             * Create vertical point cloud
             * for each plant.
             */
            for (
              let pointIndex = 0;
              pointIndex < POINTS_PER_PLANT;
              pointIndex++
            ) {
              const verticalT =
                pointIndex /
                (POINTS_PER_PLANT - 1);

              /*
               * Main vertical shape.
               */
              const pointY =
                y -
                verticalT *
                  plantHeight;

              /*
               * Small alternating side movement
               * makes it look less like a straight
               * stick and more plant-like.
               */
              const sideDirection =
                pointIndex % 2 === 0
                  ? -1
                  : 1;

              const pointX =
                x +
                sideDirection *
                  plantWidth *
                  Math.sin(
                    verticalT * Math.PI
                  );

              const point = new Graphics();

              const radius =
                0.7 +
                perspective * 1.45;

              const baseAlpha =
                0.18 +
                perspective * 0.45;

              point
                .circle(
                  0,
                  0,
                  radius
                )
                .fill({
                  color: 0x92d978,
                  alpha: baseAlpha,
                });

              point.position.set(
                pointX,
                pointY
              );

              pixiApp.stage.addChild(
                point
              );

              plantPoints.push({
                graphic: point,
                baseX: pointX,
                baseY: pointY,
                phase:
                  Math.random() *
                  Math.PI *
                  2,
                swayAmount:
                  0.3 +
                  perspective *
                    2.2,
                baseAlpha,
              });
            }

            /*
             * Add a few side points to give
             * the plant more volume.
             */
            if (
              perspective > 0.2
            ) {
              const sidePointCount = 3;

              for (
                let side = 0;
                side <
                sidePointCount;
                side++
              ) {
                const sideHeight =
                  0.25 +
                  Math.random() *
                    0.55;

                const direction =
                  side % 2 === 0
                    ? -1
                    : 1;

                const pointX =
                  x +
                  direction *
                    plantWidth *
                    (1.2 +
                      Math.random());

                const pointY =
                  y -
                  plantHeight *
                    sideHeight;

                const point =
                  new Graphics();

                const radius =
                  0.6 +
                  perspective *
                    1.1;

                const baseAlpha =
                  0.14 +
                  perspective *
                    0.35;

                point
                  .circle(
                    0,
                    0,
                    radius
                  )
                  .fill({
                    color:
                      0xa8e38f,
                    alpha:
                      baseAlpha,
                  });

                point.position.set(
                  pointX,
                  pointY
                );

                pixiApp.stage.addChild(
                  point
                );

                plantPoints.push({
                  graphic:
                    point,
                  baseX:
                    pointX,
                  baseY:
                    pointY,
                  phase:
                    Math.random() *
                    Math.PI *
                    2,
                  swayAmount:
                    0.4 +
                    perspective *
                      2.5,
                  baseAlpha,
                });
              }
            }
          }
        }

        /*
         * =========================
         * PERSPECTIVE GRID
         * =========================
         */

        gridLayer.clear();

        /*
         * Crop row lines.
         *
         * These all converge toward the
         * centre horizon.
         */
        for (
          let row = 0;
          row < CROP_ROWS;
          row++
        ) {
          const rowOffset =
            (row -
              (CROP_ROWS - 1) /
                2) *
            ROW_SPACING;

          gridLayer
            .moveTo(
              centreX,
              horizonY
            )
            .lineTo(
              centreX +
                rowOffset,
              bottomY
            )
            .stroke({
              width: 1,
              color: 0x78c86b,
              alpha: 0.13,
            });
        }

        /*
         * Horizontal perspective lines.
         */
        const DEPTH_LINES = 18;

        for (
          let i = 0;
          i < DEPTH_LINES;
          i++
        ) {
          const t =
            i /
            (DEPTH_LINES - 1);

          const perspective =
            Math.pow(t, 1.75);

          const y =
            horizonY +
            perspective *
              (bottomY -
                horizonY);

          const halfWidth =
            width *
            0.56 *
            perspective;

          gridLayer
            .moveTo(
              centreX -
                halfWidth,
              y
            )
            .lineTo(
              centreX +
                halfWidth,
              y
            )
            .stroke({
              width: 1,
              color: 0x78c86b,
              alpha:
                0.035 +
                perspective *
                  0.06,
            });
        }

        /*
         * =========================
         * ANIMATION
         * =========================
         */

        let time = 0;

        pixiApp.ticker.add(
          (ticker) => {
            time +=
              ticker.deltaTime *
              0.02;

            for (
              const point of
              plantPoints
            ) {
              /*
               * Very small sideways crop sway.
               */
              point.graphic.x =
                point.baseX +
                Math.sin(
                  time +
                    point.phase
                ) *
                  point.swayAmount;

              /*
               * Slow holographic shimmer.
               */
              const pulse =
                Math.sin(
                  time * 1.4 +
                    point.phase
                ) * 0.09;

              point.graphic.alpha =
                Math.max(
                  0.08,
                  point.baseAlpha +
                    pulse
                );
            }
          }
        );
      } catch (error) {
        console.error(
          "Pixi failed to initialise:",
          error
        );
      }
    }

    startPixi();

    return () => {
      cancelled = true;

      if (app) {
        app.destroy(true, {
          children: true,
        });

        app = null;
      }
    };
  }, []);

  return (
    <div
      ref={containerRef}
      className="pixi-stage"
    />
  );
}