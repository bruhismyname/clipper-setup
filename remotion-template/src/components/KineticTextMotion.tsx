import React from "react";
import {
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

export type KineticTextItem = {
  text: string;
  startFrame: number;
  endFrame: number;
  color?: string;
  type?: "slam" | "mask-reveal" | "glitch" | "badge";
  position?: "center" | "upper" | "lower";
  tag?: string;
};

export const KineticTextMotion: React.FC<{
  items?: KineticTextItem[];
}> = ({ items = [] }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const activeItem = items.find(
    (item) => frame >= item.startFrame && frame <= item.endFrame
  );

  if (!activeItem) return null;

  const age = frame - activeItem.startFrame;
  const remaining = activeItem.endFrame - frame;

  const textColor = activeItem.color || "#FFE600";
  const posTop =
    activeItem.position === "upper"
      ? 480
      : activeItem.position === "lower"
      ? 1200
      : 880;

  // 1. MASK REVEAL (Gozmotion / Usman Explains Clean Editorial Slide-Up)
  if (activeItem.type === "mask-reveal") {
    const slideSpring = spring({
      frame: age,
      fps,
      config: { damping: 14, stiffness: 160, mass: 0.8 },
    });
    const translateY = interpolate(slideSpring, [0, 1], [100, 0]);
    const exitOpacity = interpolate(remaining, [0, 6], [0, 1], { extrapolateLeft: "clamp" });

    return (
      <div
        style={{
          position: "absolute",
          top: posTop,
          left: "50%",
          transform: "translate(-50%, -50%)",
          zIndex: 56,
          opacity: exitOpacity,
          textAlign: "center",
          pointerEvents: "none",
          overflow: "hidden", // Clean mask container
          padding: "8px 16px",
        }}
      >
        <div
          style={{
            transform: `translateY(${translateY}%)`,
            display: "inline-flex",
            flexDirection: "column",
            alignItems: "center",
            backgroundColor: "#0D0E12",
            border: `2px solid ${textColor}`,
            borderRadius: 20,
            padding: "16px 32px",
            boxShadow: `0 24px 65px rgba(0,0,0,0.9), 0 0 35px ${textColor}55`,
            maxWidth: 820,
          }}
        >
          {activeItem.tag && (
            <span
              style={{
                fontFamily: "'SF Mono', Monaco, monospace",
                fontSize: 12,
                fontWeight: 800,
                color: textColor,
                letterSpacing: "2px",
                textTransform: "uppercase",
                marginBottom: 4,
              }}
            >
              [{activeItem.tag}]
            </span>
          )}
          <span
            style={{
              fontSize: 58,
              fontWeight: 950,
              color: "#FFFFFF",
              letterSpacing: "-0.5px",
              textTransform: "uppercase",
              wordBreak: "break-word",
              lineHeight: 1.15,
            }}
          >
            {activeItem.text}
          </span>
        </div>
      </div>
    );
  }

  // 2. SLAM IMPACT TYPOGRAPHY (Original Punchy Mode)
  const impactSpring = spring({
    frame: age,
    fps,
    config: { damping: 9, stiffness: 220, mass: 0.6 },
  });

  const scale = interpolate(impactSpring, [0, 1], [2.2, 1]);
  const enterOpacity = interpolate(age, [0, 3], [0, 1], { extrapolateRight: "clamp" });
  const exitOpacity = interpolate(remaining, [0, 6], [0, 1], { extrapolateLeft: "clamp" });
  const opacity = Math.min(enterOpacity, exitOpacity);

  return (
    <div
      style={{
        position: "absolute",
        top: posTop,
        left: "50%",
        transform: `translate(-50%, -50%) scale(${scale})`,
        zIndex: 56,
        opacity,
        textAlign: "center",
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          display: "inline-block",
          backgroundColor: "#000000",
          color: textColor,
          padding: "16px 36px",
          borderRadius: 24,
          border: `4px solid ${textColor}`,
          fontSize: 64,
          fontWeight: 950,
          letterSpacing: "-1px",
          textTransform: "uppercase",
          boxShadow: `0 20px 60px rgba(0,0,0,0.95), 0 0 45px ${textColor}80`,
          maxWidth: 820,
          wordBreak: "break-word",
          lineHeight: 1.15,
        }}
      >
        {activeItem.text}
      </div>
    </div>
  );
};
