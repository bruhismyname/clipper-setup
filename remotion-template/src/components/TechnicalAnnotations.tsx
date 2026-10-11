import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";

/**
 * TechnicalAnnotations (Gozmotion Stylized Shapes & Editorial Callouts)
 * Adds documentary viewfinder corner brackets, monospace reference tags,
 * and delicate data lines around the central 860px video card.
 */
export const TechnicalAnnotations: React.FC<{
  enabled?: boolean;
  docTag?: string;
  sourceCredit?: string;
}> = ({
  enabled = true,
  docTag = "DOC_REF #9042",
  sourceCredit = "UNCENSORED RECORDING",
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  if (!enabled) return null;

  const enterSpring = spring({
    frame,
    fps,
    config: { damping: 12, stiffness: 140 },
  });

  const opacity = interpolate(enterSpring, [0, 1], [0, 0.85]);

  return (
    <div
      style={{
        position: "absolute",
        top: "47%",
        left: "50%",
        transform: "translate(-50%, -50%)",
        width: 890, // Slightly larger than 860px video card to frame it with brackets
        height: 515,
        pointerEvents: "none",
        zIndex: 37,
        opacity,
      }}
    >
      {/* 1. Top-Left Viewfinder Bracket */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          width: 18,
          height: 18,
          borderTop: "2px solid rgba(255, 255, 255, 0.45)",
          borderLeft: "2px solid rgba(255, 255, 255, 0.45)",
        }}
      />

      {/* 2. Top-Right Viewfinder Bracket */}
      <div
        style={{
          position: "absolute",
          top: 0,
          right: 0,
          width: 18,
          height: 18,
          borderTop: "2px solid rgba(255, 255, 255, 0.45)",
          borderRight: "2px solid rgba(255, 255, 255, 0.45)",
        }}
      />

      {/* 3. Bottom-Left Viewfinder Bracket */}
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          width: 18,
          height: 18,
          borderBottom: "2px solid rgba(255, 255, 255, 0.45)",
          borderLeft: "2px solid rgba(255, 255, 255, 0.45)",
        }}
      />

      {/* 4. Bottom-Right Viewfinder Bracket */}
      <div
        style={{
          position: "absolute",
          bottom: 0,
          right: 0,
          width: 18,
          height: 18,
          borderBottom: "2px solid rgba(255, 255, 255, 0.45)",
          borderRight: "2px solid rgba(255, 255, 255, 0.45)",
        }}
      />

      {/* 5. Minimalist Technical Monospace Tag (Top Right) */}
      <div
        style={{
          position: "absolute",
          top: -24,
          right: 4,
          fontFamily: "'SF Mono', Monaco, Consolas, monospace",
          fontSize: 11,
          fontWeight: 700,
          letterSpacing: "1px",
          color: "rgba(255, 255, 255, 0.5)",
          textTransform: "uppercase",
        }}
      >
        [{docTag}]
      </div>

      {/* 6. Minimalist Technical Monospace Source Tag (Bottom Right) */}
      <div
        style={{
          position: "absolute",
          bottom: -24,
          right: 4,
          fontFamily: "'SF Mono', Monaco, Consolas, monospace",
          fontSize: 10,
          fontWeight: 600,
          letterSpacing: "0.8px",
          color: "rgba(255, 255, 255, 0.4)",
          textTransform: "uppercase",
        }}
      >
        SOURCE // {sourceCredit}
      </div>
    </div>
  );
};
