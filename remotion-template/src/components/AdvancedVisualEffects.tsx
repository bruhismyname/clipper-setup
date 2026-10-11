import React from "react";
import { AbsoluteFill, interpolate } from "remotion";

export type AdvancedVisualEffectsConfig = {
  enabled?: boolean;
  vignette?: boolean;
  chromaticAberration?: boolean;
  lightLeak?: boolean;
  filmGrain?: boolean;
};

/**
 * 1. DYNAMIC CINEMATIC VIGNETTE
 * Directs viewer focus to the center safe zone and masks edge harshness.
 */
export const DynamicCinematicVignette: React.FC<{
  intensity?: number;
}> = ({ intensity = 0.72 }) => {
  return (
    <AbsoluteFill
      style={{
        pointerEvents: "none",
        zIndex: 85,
        background: `radial-gradient(ellipse at 50% 48%, transparent 42%, rgba(0, 0, 0, ${intensity}) 100%)`,
        mixBlendMode: "multiply",
      }}
    />
  );
};

/**
 * 2. CHROMATIC ABERRATION PULSE
 * High-end optical effect: subtle RGB spectral fringing during moments of impact.
 */
export const ChromaticAberrationPulse: React.FC<{
  frame: number;
  triggerFrames?: number[];
}> = ({ frame, triggerFrames = [0] }) => {
  // Check if current frame is close to any trigger frame (within 8 frames)
  const activeTrigger = triggerFrames.find(
    (tf) => frame >= tf && frame <= tf + 8
  );

  if (activeTrigger === undefined) return null;

  const age = frame - activeTrigger;
  const offset = interpolate(age, [0, 2, 8], [0, 3.5, 0], {
    extrapolateRight: "clamp",
  });
  const opacity = interpolate(age, [0, 2, 8], [0, 0.45, 0], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        pointerEvents: "none",
        zIndex: 88,
        mixBlendMode: "screen",
        opacity,
      }}
    >
      {/* Cyan Channel */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          transform: `translate(${-offset}px, 0)`,
          background: "rgba(0, 255, 255, 0.08)",
          filter: "blur(1px)",
        }}
      />
      {/* Red Channel */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          transform: `translate(${offset}px, 0)`,
          background: "rgba(255, 0, 80, 0.08)",
          filter: "blur(1px)",
        }}
      />
    </AbsoluteFill>
  );
};

/**
 * 3. ANAMORPHIC LIGHT LEAK SWEEP
 * Soft cinematic streak of light gliding horizontally across the frame
 * to enhance visual transitions and evoke anamorphic cine-lenses.
 */
export const AnamorphicLightLeak: React.FC<{
  frame: number;
  startFrame?: number;
  duration?: number;
}> = ({ frame, startFrame = 0, duration = 30 }) => {
  if (frame < startFrame || frame > startFrame + duration) return null;

  const age = frame - startFrame;
  const progress = age / duration;

  // Move horizontally across screen
  const posX = interpolate(progress, [0, 1], [-400, 1480]);
  const opacity = interpolate(progress, [0, 0.3, 0.7, 1], [0, 0.35, 0.35, 0], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        pointerEvents: "none",
        zIndex: 87,
        overflow: "hidden",
        mixBlendMode: "screen",
        opacity,
      }}
    >
      <div
        style={{
          position: "absolute",
          top: "40%",
          left: posX,
          width: 500,
          height: 350,
          background:
            "radial-gradient(ellipse at center, rgba(255, 230, 120, 0.7) 0%, rgba(255, 100, 50, 0.3) 50%, transparent 80%)",
          transform: "translate(-50%, -50%) rotate(-18deg) scaleX(2.2)",
          filter: "blur(40px)",
        }}
      />
    </AbsoluteFill>
  );
};

/**
 * 4. MULTI-OCTAVE ORGANIC FILM GRAIN (Anti-AI Slop V2)
 * High-frequency subtle noise that completely dissolves AI smoothness
 * and gives authentic 35mm film stock feeling.
 */
export const FilmGrainOverlayV2: React.FC<{
  opacity?: number;
}> = ({ opacity = 0.085 }) => {
  return (
    <AbsoluteFill
      style={{
        pointerEvents: "none",
        zIndex: 95,
        mixBlendMode: "overlay",
        opacity,
      }}
    >
      <svg width="100%" height="100%">
        <filter id="proGrainFilter">
          <feTurbulence
            type="fractalNoise"
            baseFrequency="0.88"
            numOctaves="4"
            stitchTiles="stitch"
          />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="100%" height="100%" filter="url(#proGrainFilter)" />
      </svg>
    </AbsoluteFill>
  );
};
