import React from "react";
import { AbsoluteFill, OffthreadVideo, useCurrentFrame, useVideoConfig } from "remotion";

/* -------------------------------------------------------------
 * SPEAKER CROP LAYER (Style B "Fullbleed Speaker")
 * Fills the 9:16 canvas with a window of the 16:9 episode footage.
 * Each segment frames one person (centerX = face position as a fraction
 * of the source width); switching segments is a hard cut, like the
 * reaction cuts used by fan clip pages. Crop positions come from
 * crop-plan.json (hook-radar/scripts/crop_plan.py), set per shot by hand,
 * never by an AI auto-reframe.
 * ------------------------------------------------------------- */

export type SpeakerCropSegment = {
  from: number;
  to: number;
  /** Horizontal face position in the source frame, 0 (left) – 1 (right) */
  centerX: number;
  /** Vertical anchor, 0 (top) – 1 (bottom). 0.5 keeps the full height when zoom = 1 */
  centerY?: number;
  /** 1 = full source height; >1 punches in */
  zoom?: number;
  who?: "host" | "guest" | "other" | "";
};

const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));

export const SpeakerCropLayer: React.FC<{
  src: string;
  segments: SpeakerCropSegment[];
  sourceWidth: number;
  sourceHeight: number;
}> = ({ src, segments, sourceWidth, sourceHeight }) => {
  const frame = useCurrentFrame();
  const { width, height } = useVideoConfig();

  const seg =
    segments.find((s) => frame >= s.from && frame < s.to) ??
    segments[segments.length - 1] ?? { from: 0, to: Infinity, centerX: 0.5 };

  const zoom = Math.max(1, seg.zoom ?? 1);
  // Scale so the source height fills the canvas height (times zoom)
  const videoH = height * zoom;
  const videoW = (sourceWidth / sourceHeight) * videoH;
  const left = clamp(width / 2 - seg.centerX * videoW, width - videoW, 0);
  const top = clamp(height / 2 - (seg.centerY ?? 0.5) * videoH, height - videoH, 0);

  if (!src) return <AbsoluteFill style={{ backgroundColor: "#000" }} />;

  return (
    <AbsoluteFill style={{ backgroundColor: "#000", overflow: "hidden" }}>
      <OffthreadVideo
        src={src}
        style={{
          position: "absolute",
          width: videoW,
          height: videoH,
          left,
          top,
          maxWidth: "none",
        }}
      />
    </AbsoluteFill>
  );
};

/** Share of frames framed on the host, for the campaign's ≥20% host rule */
export const hostShare = (segments: SpeakerCropSegment[], durationInFrames: number) => {
  const hostFrames = segments
    .filter((s) => s.who === "host")
    .reduce((acc, s) => acc + Math.max(0, Math.min(s.to, durationInFrames) - s.from), 0);
  return durationInFrames > 0 ? hostFrames / durationInFrames : 0;
};
