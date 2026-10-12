import React from "react";

export type TalkingHeadConfig = {
  enabled?: boolean;
  speakerName?: string;
  speakerTag?: string;
  avatarSrc?: string;
  position?: "bottom-left" | "bottom-right" | "top-left" | "top-right";
  glowColor?: string;
  dynamicPunchZoom?: boolean;
};

export const TalkingHeadBadge: React.FC<{
  config?: TalkingHeadConfig;
  frame: number;
  fps: number;
}> = ({ config, frame, fps }) => {
  if (!config || config.enabled === false || !config.speakerName) return null;

  const glowColor = config.glowColor || "#FFE600";
  const position = config.position || "bottom-left";

  // "bottom" sits in the gap between the video card (ends ~Y 1150) and the subtitle band (Y 1350-1450)
  const posStyle: React.CSSProperties =
    position === "bottom-left"
      ? { top: 1190, left: 110 }
      : position === "bottom-right"
      ? { top: 1190, right: 110 }
      : position === "top-left"
      ? { top: 615, left: 110 }
      : { top: 615, right: 110 };

  // Subtle breathing pulse for speaker indicator
  const pulse = Math.sin(frame * 0.15) * 0.15 + 0.85;

  return (
    <div
      style={{
        position: "absolute",
        zIndex: 46,
        display: "flex",
        alignItems: "center",
        gap: 12,
        backgroundColor: "rgba(15, 23, 42, 0.92)",
        backdropFilter: "blur(14px)",
        border: `2px solid ${glowColor}`,
        borderRadius: 30,
        padding: "8px 20px 8px 12px",
        boxShadow: `0 12px 30px rgba(0,0,0,0.8), 0 0 20px ${glowColor}40`,
        ...posStyle,
      }}
    >
      {/* Live Mic / Speaker Pulse Dot */}
      <div
        style={{
          width: 14,
          height: 14,
          borderRadius: "50%",
          backgroundColor: glowColor,
          boxShadow: `0 0 12px ${glowColor}`,
          transform: `scale(${pulse})`,
        }}
      />

      <div style={{ display: "flex", flexDirection: "column" }}>
        <span
          style={{
            color: "#FFFFFF",
            fontSize: 18,
            fontWeight: 900,
            letterSpacing: "-0.3px",
            textTransform: "uppercase",
            lineHeight: 1.1,
          }}
        >
          {config.speakerName}
        </span>
        {config.speakerTag && (
          <span
            style={{
              color: glowColor,
              fontSize: 12,
              fontWeight: 800,
              letterSpacing: "1px",
              textTransform: "uppercase",
            }}
          >
            {config.speakerTag}
          </span>
        )}
      </div>
    </div>
  );
};
