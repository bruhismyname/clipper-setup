import React from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";

/**
 * EditorialGridBackground (Gozmotion / Usman Explains Aesthetic)
 * Clean, minimal architectural gridlines, corner crosshairs (+),
 * and subtle technical metadata stamps that evoke high-end Vox/Bloomberg documentaries.
 */
export const EditorialGridBackground: React.FC<{
  enabled?: boolean;
  opacity?: number;
}> = ({ enabled = true, opacity = 0.22 }) => {
  const frame = useCurrentFrame();

  if (!enabled) return null;

  // Subtle pulsing technical indicator
  const blink = Math.floor(frame / 20) % 2 === 0;

  return (
    <AbsoluteFill
      style={{
        pointerEvents: "none",
        zIndex: 10,
        overflow: "hidden",
      }}
    >
      {/* 1. Fine SVG Grid Lines (120px step) */}
      <svg
        width="1080"
        height="1920"
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          opacity,
        }}
      >
        <defs>
          <pattern
            id="editorialGridPattern"
            width="120"
            height="120"
            patternUnits="userSpaceOnUse"
          >
            <path
              d="M 120 0 L 0 0 0 120"
              fill="none"
              stroke="#FFFFFF"
              strokeWidth="0.8"
              strokeDasharray="3 6"
              strokeOpacity="0.45"
            />
          </pattern>
        </defs>
        <rect width="1080" height="1920" fill="url(#editorialGridPattern)" />
      </svg>

      {/* 2. Four Corner Crosshairs (+) inside Safe Margins */}
      {[
        { top: 295, left: 110 },
        { top: 295, right: 110 },
        { bottom: 400, left: 110 },
        { bottom: 400, right: 110 },
      ].map((pos, idx) => (
        <div
          key={idx}
          style={{
            position: "absolute",
            width: 14,
            height: 14,
            opacity: 0.45,
            ...pos,
          }}
        >
          {/* Horizontal line */}
          <div
            style={{
              position: "absolute",
              top: 6,
              left: 0,
              width: 14,
              height: 1.5,
              backgroundColor: "#FFFFFF",
            }}
          />
          {/* Vertical line */}
          <div
            style={{
              position: "absolute",
              top: 0,
              left: 6,
              width: 1.5,
              height: 14,
              backgroundColor: "#FFFFFF",
            }}
          />
        </div>
      ))}

      {/* 3. Top Technical Header Stamp (Monospace Aesthetic) */}
      <div
        style={{
          position: "absolute",
          top: 268,
          left: 110,
          right: 110,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontFamily: "'SF Mono', Monaco, Consolas, monospace",
          fontSize: 11,
          color: "rgba(255, 255, 255, 0.4)",
          letterSpacing: "1.5px",
          textTransform: "uppercase",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span
            style={{
              width: 6,
              height: 6,
              borderRadius: "50%",
              backgroundColor: blink ? "#CCFF00" : "#555555",
              boxShadow: blink ? "0 0 6px #CCFF00" : "none",
            }}
          />
          <span>[SYSTEM // ARCHIVE_01]</span>
        </div>
        <span>ASPECT: 9:16 // FPS: 30</span>
      </div>
    </AbsoluteFill>
  );
};
