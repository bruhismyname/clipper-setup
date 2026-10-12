import React from "react";
import { Easing, Img, Sequence, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";

/* -------------------------------------------------------------
 * KEYWORD OVERLAY LAYER (Style B "Fullbleed Speaker")
 * A "visual dictionary": when the speaker names a thing, its picture pops
 * into the lower half of the frame for 1–2.5 s, leaving the face visible.
 * Assets come from public/overlays (overlay_fetch.py: Noto emoji, Openverse /
 * Pixabay photos with the anti-AI filter, real screenshots, episode frames).
 * ------------------------------------------------------------- */

export type KeywordOverlayItem = {
  /** Path inside public/, e.g. overlays/avocado-01.jpg or overlays/emoji/emoji_u1f914.png */
  src: string;
  from: number;
  duration: number;
  /** photo = rounded rectangle; png/emoji = no frame (transparent asset) */
  kind?: "photo" | "png" | "emoji";
  /** License credit, shown small under CC BY / CC BY-SA photos */
  credit?: string;
};

export const OVERLAY_ZONE = { top: 960, bottom: 1440, maxWidth: 820 };

const toPublic = (src: string) => {
  if (src.startsWith("http://") || src.startsWith("https://")) return src;
  return staticFile(src.replace(/\\/g, "/").replace(/^public\//, ""));
};

const OverlayCard: React.FC<{ item: KeywordOverlayItem }> = ({ item }) => {
  const frame = useCurrentFrame();
  const kind = item.kind ?? "photo";
  const zoneH = OVERLAY_ZONE.bottom - OVERLAY_ZONE.top;
  const exitStart = Math.max(6, item.duration - 4);

  const scale = interpolate(frame, [0, 6], [0.6, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.bezier(0.34, 1.56, 0.64, 1),
  });
  const opacity = Math.min(
    interpolate(frame, [0, 3], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
    interpolate(frame, [exitStart, item.duration], [1, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
  );

  const isEmoji = kind === "emoji";
  return (
    <div
      style={{
        position: "absolute",
        top: OVERLAY_ZONE.top,
        left: 0,
        right: 0,
        height: zoneH,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        opacity,
        scale,
      }}
    >
      <Img
        src={toPublic(item.src)}
        style={{
          maxWidth: isEmoji ? 380 : OVERLAY_ZONE.maxWidth,
          maxHeight: isEmoji ? 380 : zoneH - (item.credit ? 34 : 0),
          objectFit: "contain",
          borderRadius: kind === "photo" ? 28 : 0,
          boxShadow: kind === "photo" ? "0 18px 40px rgba(0,0,0,0.45)" : undefined,
          filter: kind === "photo" ? undefined : "drop-shadow(0 12px 24px rgba(0,0,0,0.4))",
        }}
      />
      {item.credit ? (
        <div
          style={{
            marginTop: 8,
            maxWidth: OVERLAY_ZONE.maxWidth,
            fontFamily: "system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif",
            fontSize: 18,
            color: "rgba(255,255,255,0.85)",
            textShadow: "0 1px 4px rgba(0,0,0,0.9)",
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
          }}
        >
          {item.credit}
        </div>
      ) : null}
    </div>
  );
};

export const KeywordOverlayLayer: React.FC<{ overlays: KeywordOverlayItem[]; hideFrom?: number }> = ({
  overlays,
  hideFrom = Infinity,
}) => {
  const { fps } = useVideoConfig();
  return (
    <>
      {overlays
        .filter((o) => o.from < hideFrom)
        .map((o, i) => (
          <Sequence
            key={`${o.src}-${o.from}-${i}`}
            name={`overlay:${o.src.split("/").pop()}`}
            from={o.from}
            durationInFrames={Math.max(1, Math.min(o.duration, hideFrom - o.from))}
            premountFor={fps}
          >
            <OverlayCard item={o} />
          </Sequence>
        ))}
    </>
  );
};
