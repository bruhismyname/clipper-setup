import React from "react";
import { Easing, interpolate, useCurrentFrame } from "remotion";
import { loadFont } from "@remotion/google-fonts/Montserrat";

/* -------------------------------------------------------------
 * MINIMAL OUTRO CTA (Style B "Fullbleed Speaker")
 * The campaign requires a YouTube redirect at the very end (rules.md §4).
 * Style B keeps it in the caption language instead of a big end card:
 * one caption-styled line plus a small red YouTube pill with the channel.
 * ------------------------------------------------------------- */

const { fontFamily } = loadFont("normal", { weights: ["700", "800"], subsets: ["latin"] });

export type MinimalOutroCtaConfig = {
  enabled?: boolean;
  channelName?: string;
  seriesName?: string;
  ctaText?: string;
  /** Length in frames, counted back from the end of the clip */
  durationInFrames?: number;
};

export const MinimalOutroCta: React.FC<{ config: MinimalOutroCtaConfig }> = ({ config }) => {
  const frame = useCurrentFrame();
  const {
    channelName = "Lyrical Lemonade TV",
    seriesName = "",
    ctaText = "watch the full episode on YouTube 👇",
  } = config;

  const enter = interpolate(frame, [0, 8], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.16, 1, 0.3, 1),
  });

  return (
    <div
      style={{
        position: "absolute",
        left: 110,
        right: 110,
        top: 1180,
        translate: `0 calc(-50% + ${(1 - enter) * 24}px)`,
        opacity: enter,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 18,
        fontFamily,
      }}
    >
      <div
        style={{
          fontWeight: 800,
          fontSize: 58,
          lineHeight: 1.1,
          color: "#FFFFFF",
          textAlign: "center",
          WebkitTextStroke: "5px #000000",
          paintOrder: "stroke fill",
          textShadow: "0 4px 12px rgba(0,0,0,0.45)",
        }}
      >
        {ctaText}
      </div>
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 14,
          padding: "14px 30px",
          borderRadius: 999,
          backgroundColor: "#FF0000",
          color: "#FFFFFF",
          fontWeight: 800,
          fontSize: 40,
          boxShadow: "0 10px 28px rgba(0,0,0,0.45)",
        }}
      >
        <svg width="40" height="28" viewBox="0 0 40 28" aria-hidden>
          <rect width="40" height="28" rx="8" fill="#FFFFFF" />
          <path d="M16 8 L27 14 L16 20 Z" fill="#FF0000" />
        </svg>
        {channelName}
      </div>
      {seriesName ? (
        <div
          style={{
            fontWeight: 700,
            fontSize: 30,
            color: "#FFFFFF",
            textAlign: "center",
            textShadow: "0 2px 8px rgba(0,0,0,0.9)",
          }}
        >
          {seriesName}
        </div>
      ) : null}
    </div>
  );
};
