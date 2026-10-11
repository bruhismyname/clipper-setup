import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

/**
 * HighlighterWipe (Gozmotion / Usman Explains Marker Technique)
 * Fluorescent marker pen / highlighter stroke that sweeps horizontally
 * underneath key phrases or keywords when spoken.
 */
export const HighlighterWipe: React.FC<{
  startFrame: number;
  durationInFrames?: number;
  color?: string;
  height?: number;
  width?: number | string;
  top?: number | string;
  left?: number | string;
}> = ({
  startFrame,
  durationInFrames = 18,
  color = "#CCFF00", // Electric Volt / Fluorescent Yellow
  height = 14,
  width = "100%",
  top = "auto",
  left = "auto",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  if (frame < startFrame) return null;

  const age = frame - startFrame;
  const wipeSpring = spring({
    frame: age,
    fps,
    config: {
      damping: 12,
      stiffness: 160,
      mass: 0.7,
    },
  });

  const progress = interpolate(wipeSpring, [0, 1], [0, 100]);

  return (
    <div
      style={{
        position: "absolute",
        bottom: 4,
        left: 0,
        width,
        height,
        backgroundColor: color,
        opacity: 0.65,
        borderRadius: 4,
        clipPath: `polygon(0 0, ${progress}% 0, ${progress}% 100%, 0 100%)`,
        mixBlendMode: "multiply",
        pointerEvents: "none",
        zIndex: -1,
      }}
    />
  );
};
