import React from "react";
import {
  OffthreadVideo,
  Img,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

export type BRollItem = {
  src: string;
  type: "video" | "image";
  mode?: "fullscreen" | "card" | "split-top" | "split-bottom";
  startFrame: number;
  endFrame: number;
  caption?: string;
  sourceCredit?: string;
  kenBurns?: boolean;
};

export const BRollLayer: React.FC<{
  brolls?: BRollItem[];
}> = ({ brolls = [] }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const activeBRoll = brolls.find(
    (b) => frame >= b.startFrame && frame <= b.endFrame,
  );

  if (!activeBRoll) return null;

  const age = frame - activeBRoll.startFrame;
  const duration = activeBRoll.endFrame - activeBRoll.startFrame;
  const remaining = activeBRoll.endFrame - frame;

  // Spring entrance & exit
  const enterSpring = spring({
    frame: age,
    fps,
    config: { damping: 12, stiffness: 140, mass: 0.8 },
  });

  const enterScale = interpolate(enterSpring, [0, 1], [0.92, 1]);
  const enterOpacity = interpolate(age, [0, 5], [0, 1], {
    extrapolateRight: "clamp",
  });
  const exitOpacity = interpolate(remaining, [0, 6], [0, 1], {
    extrapolateLeft: "clamp",
  });
  const opacity = Math.min(enterOpacity, exitOpacity);

  // Ken Burns subtle zoom effect (1.0x -> 1.07x over duration)
  const kbZoom =
    activeBRoll.kenBurns !== false
      ? interpolate(age, [0, Math.max(1, duration)], [1.0, 1.07], {
          extrapolateRight: "clamp",
        })
      : 1.0;

  const resolvedSrc = (() => {
    if (
      activeBRoll.src.startsWith("http://") ||
      activeBRoll.src.startsWith("https://")
    ) {
      return activeBRoll.src;
    }
    // "broll/x.mp4" stays a public/ subpath; absolute paths fall back to their file name in public/
    const normalized = activeBRoll.src.replace(/\\/g, "/");
    const isAbsolute =
      /^[a-zA-Z]:\//.test(normalized) || normalized.startsWith("/");
    const publicPath = normalized.includes("public/")
      ? normalized.split("public/").pop()!
      : isAbsolute
        ? normalized.split("/").pop()!
        : normalized;
    try {
      return staticFile(publicPath);
    } catch {
      return publicPath;
    }
  })();

  const mode = activeBRoll.mode || "card";

  // Card mode: Floating centered editorial card with soft glow
  if (mode === "card") {
    return (
      <div
        style={{
          position: "absolute",
          top: "46%",
          left: "50%",
          transform: `translate(-50%, -50%) scale(${enterScale})`,
          width: 840,
          aspectRatio: "16 / 10",
          zIndex: 42,
          opacity,
          borderRadius: 24,
          overflow: "hidden",
          boxShadow:
            "0 35px 80px rgba(0,0,0,0.9), 0 0 0 3px rgba(255,255,255,0.15)",
          backgroundColor: "#000000",
        }}
      >
        <div
          style={{
            width: "100%",
            height: "100%",
            transform: `scale(${kbZoom})`,
            transformOrigin: "center center",
          }}
        >
          {activeBRoll.type === "video" ? (
            <Sequence
              key={`${activeBRoll.src}-${activeBRoll.startFrame}`}
              from={activeBRoll.startFrame}
              layout="none"
            >
              <OffthreadVideo
                src={resolvedSrc}
                muted
                style={{ width: "100%", height: "100%", objectFit: "cover" }}
              />
            </Sequence>
          ) : (
            <Img
              src={resolvedSrc}
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
          )}
        </div>

        {/* Caption / Source Credit */}
        {(activeBRoll.caption || activeBRoll.sourceCredit) && (
          <div
            style={{
              position: "absolute",
              bottom: 0,
              left: 0,
              right: 0,
              background:
                "linear-gradient(180deg, transparent 0%, rgba(0,0,0,0.85) 100%)",
              padding: "24px 20px 14px 20px",
              display: "flex",
              justifyContent: "space-between",
              alignItems: "flex-end",
            }}
          >
            {activeBRoll.caption && (
              <span style={{ color: "#FFFFFF", fontSize: 18, fontWeight: 700 }}>
                {activeBRoll.caption}
              </span>
            )}
            {activeBRoll.sourceCredit && (
              <span
                style={{
                  color: "rgba(255,255,255,0.7)",
                  fontSize: 13,
                  fontWeight: 600,
                }}
              >
                {activeBRoll.sourceCredit}
              </span>
            )}
          </div>
        )}
      </div>
    );
  }

  // Fullscreen mode: Takes over central 9:16 vertical view
  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        left: 0,
        width: "100%",
        height: "100%",
        zIndex: 42,
        opacity,
        overflow: "hidden",
      }}
    >
      <div
        style={{
          width: "100%",
          height: "100%",
          transform: `scale(${kbZoom})`,
          transformOrigin: "center center",
        }}
      >
        {activeBRoll.type === "video" ? (
          <Sequence
            key={`${activeBRoll.src}-${activeBRoll.startFrame}`}
            from={activeBRoll.startFrame}
            layout="none"
          >
            <OffthreadVideo
              src={resolvedSrc}
              muted
              style={{ width: "100%", height: "100%", objectFit: "cover" }}
            />
          </Sequence>
        ) : (
          <Img
            src={resolvedSrc}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        )}
      </div>

      {activeBRoll.caption && (
        <div
          style={{
            position: "absolute",
            bottom: 240,
            left: 40,
            right: 40,
            backgroundColor: "rgba(0,0,0,0.8)",
            backdropFilter: "blur(10px)",
            borderRadius: 16,
            padding: "12px 20px",
            border: "1px solid rgba(255,255,255,0.2)",
            textAlign: "center",
          }}
        >
          <span style={{ color: "#FFE600", fontSize: 20, fontWeight: 800 }}>
            {activeBRoll.caption}
          </span>
        </div>
      )}
    </div>
  );
};
