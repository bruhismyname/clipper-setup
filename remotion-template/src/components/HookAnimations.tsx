import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
} from "remotion";

export type HookAnimationConfig = {
  enabled?: boolean;
  impactFlash?: boolean;
  cameraSlam?: boolean;
  attentionBadge?: {
    text: string;
    color?: string;
  };
};

/**
 * 1. IMPACT FLASH OVERLAY
 * High-luminance exposure flash in the first 6 frames (0.2s)
 * immediately halts the user's scroll / swipe thumb.
 */
export const HookImpactFlash: React.FC<{ frame: number }> = ({ frame }) => {
  if (frame > 7) return null;

  const flashOpacity = interpolate(
    frame,
    [0, 1, 6],
    [0.75, 0.45, 0.0],
    { extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#FFFFFF",
        opacity: flashOpacity,
        pointerEvents: "none",
        zIndex: 90,
        mixBlendMode: "screen",
      }}
    />
  );
};

/**
 * 2. CAMERA SLAM & MICRO-SHAKE
 * Fast snap-in zoom (1.14x -> 1.0x) with elastic spring bounce
 * and organic camera jitter on impact (frame 0-14).
 */
export const useHookCameraSlam = (frame: number, fps: number, enabled: boolean = true) => {
  if (!enabled || frame > 20) {
    return { scale: 1.0, offsetX: 0, offsetY: 0 };
  }

  const slamSpring = spring({
    frame,
    fps,
    config: {
      damping: 10,
      stiffness: 180,
      mass: 0.6,
    },
  });

  const scale = interpolate(slamSpring, [0, 1], [1.14, 1.0]);

  // Micro camera jitter on initial landing (frames 2 to 8)
  const shakeDecay = interpolate(frame, [0, 8], [1, 0], { extrapolateRight: "clamp" });
  const offsetX = Math.sin(frame * 3.8) * 5 * shakeDecay;
  const offsetY = Math.cos(frame * 4.2) * 5 * shakeDecay;

  return { scale, offsetX, offsetY };
};

/**
 * 3. ATTENTION TRIGGER BADGE (Detik 0 - 3)
 * Floating attention badge placed inside the top safe zone
 * with an urgent pulsing glow to maximize 3-second retention.
 */
export const AttentionTriggerBadge: React.FC<{
  badge?: { text: string; color?: string };
  frame: number;
  fps: number;
}> = ({ badge, frame, fps }) => {
  if (!badge || !badge.text) return null;
  // Active only during the critical hook window (first 90 frames = 3.0 seconds)
  if (frame > 90) return null;

  const age = frame;
  const enterSpring = spring({
    frame: age,
    fps,
    config: { damping: 10, stiffness: 160, mass: 0.7 },
  });

  const scale = interpolate(enterSpring, [0, 1], [0.6, 1.0]);
  const exitOpacity = interpolate(90 - frame, [0, 10], [0, 1], { extrapolateLeft: "clamp" });

  const pulse = Math.sin(frame * 0.35) * 0.04 + 1.0;
  const badgeColor = badge.color || "#FF3B30";

  return (
    <div
      style={{
        position: "absolute",
        top: 295,
        left: "50%",
        transform: `translateX(-50%) scale(${scale * pulse})`,
        zIndex: 55,
        opacity: exitOpacity,
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          backgroundColor: "rgba(15, 23, 42, 0.92)",
          border: `2px solid ${badgeColor}`,
          borderRadius: 20,
          padding: "6px 18px",
          boxShadow: `0 8px 25px ${badgeColor}66, 0 0 12px ${badgeColor}44`,
          backdropFilter: "blur(12px)",
        }}
      >
        <span
          style={{
            width: 10,
            height: 10,
            borderRadius: "50%",
            backgroundColor: badgeColor,
            boxShadow: `0 0 10px ${badgeColor}`,
          }}
        />
        <span
          style={{
            color: "#FFFFFF",
            fontSize: 18,
            fontWeight: 900,
            letterSpacing: "1.2px",
            textTransform: "uppercase",
          }}
        >
          {badge.text}
        </span>
      </div>
    </div>
  );
};
