import React from "react";
import { AbsoluteFill } from "remotion";

export type BodyAnimationConfig = {
  enabled?: boolean;
  retentionProgressBar?: boolean;
  ambientCameraDrift?: boolean;
  floatingParticles?: boolean;
};

/**
 * 1. RETENTION PROGRESS BAR (Scrubber)
 * Psychological engagement tool: A glowing gradient line that fills from 0% to 100%
 * visually cues the viewer that the clip is short and worth completing.
 */
export const RetentionProgressBar: React.FC<{
  currentFrame: number;
  durationInFrames: number;
  width?: number;
  top?: number | string;
}> = ({
  currentFrame,
  durationInFrames,
  width = 860,
  top = "calc(47% + 252px)", // Placed exactly below the 860px 16:9 card
}) => {
  const progress = Math.min(1, Math.max(0, currentFrame / Math.max(1, durationInFrames)));
  const progressPercent = `${(progress * 100).toFixed(2)}%`;

  return (
    <div
      style={{
        position: "absolute",
        top,
        left: "50%",
        transform: "translateX(-50%)",
        width,
        height: 6,
        backgroundColor: "rgba(255, 255, 255, 0.12)",
        borderRadius: 4,
        overflow: "hidden",
        zIndex: 38,
        boxShadow: "0 2px 8px rgba(0, 0, 0, 0.5)",
      }}
    >
      <div
        style={{
          width: progressPercent,
          height: "100%",
          background: "linear-gradient(90deg, #FFE600 0%, #FF3B30 70%, #00F5D4 100%)",
          borderRadius: 4,
          boxShadow: "0 0 12px rgba(255, 230, 0, 0.8)",
          transition: "width 0.05s linear",
        }}
      />
    </div>
  );
};

/**
 * 2. AMBIENT CAMERA DRIFT (Breathing Camera Motion)
 * Subtly modulates scale and position using two out-of-phase sine waves
 * so the footage never feels like a static still photo.
 */
export const useAmbientCameraDrift = (frame: number, enabled: boolean = true) => {
  if (!enabled) {
    return { driftScale: 1.0, driftX: 0, driftY: 0 };
  }

  // Smooth sinusoidal cycles
  const driftScale = 1.0 + Math.sin(frame * 0.04) * 0.012; // 1.000 to 1.012
  const driftX = Math.sin(frame * 0.025) * 3.0; // +/- 3px
  const driftY = Math.cos(frame * 0.035) * 2.5; // +/- 2.5px

  return { driftScale, driftX, driftY };
};

/**
 * 3. FLOATING AMBIENT PARTICLES (Cinematic Embers / Bokeh)
 * Soft, low-opacity dust particles floating slowly across the depth layers
 * breaking up digital flatness and giving high-end organic cinema texture.
 */
export const FloatingAmbientParticles: React.FC<{ frame: number; count?: number }> = ({
  frame,
  count = 14,
}) => {
  const particles = React.useMemo(() => {
    return Array.from({ length: count }).map((_, i) => {
      const seedX = ((i * 73 + 17) % 100) / 100;
      const seedY = ((i * 47 + 29) % 100) / 100;
      const size = 3 + (i % 5) * 2;
      const speed = 0.4 + (i % 3) * 0.3;
      const opacityBase = 0.15 + (i % 4) * 0.08;
      return { seedX, seedY, size, speed, opacityBase, id: i };
    });
  }, [count]);

  return (
    <AbsoluteFill
      style={{
        pointerEvents: "none",
        zIndex: 25,
        overflow: "hidden",
      }}
    >
      {particles.map((p) => {
        const posX = (p.seedX * 1080 + Math.sin((frame * 0.02 + p.id) * p.speed) * 40) % 1080;
        const posY =
          (p.seedY * 1920 - frame * p.speed * 1.2 + 1920 * 10) % 1920;
        const pulse = Math.sin((frame * 0.05 + p.id) * p.speed) * 0.08 + p.opacityBase;

        return (
          <div
            key={p.id}
            style={{
              position: "absolute",
              left: posX,
              top: posY,
              width: p.size,
              height: p.size,
              borderRadius: "50%",
              backgroundColor: "#FFE600",
              opacity: Math.max(0, Math.min(0.5, pulse)),
              boxShadow: `0 0 ${p.size * 2}px rgba(255, 230, 0, 0.6)`,
              filter: "blur(1px)",
            }}
          />
        );
      })}
    </AbsoluteFill>
  );
};
