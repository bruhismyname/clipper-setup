import React from "react";
import {
  AbsoluteFill,
  CalculateMetadataFunction,
  Composition,
  Img,
  OffthreadVideo,
  Sequence,
  staticFile,
  useVideoConfig,
} from "remotion";
import { SpeakerCropLayer, SpeakerCropSegment } from "./components/SpeakerCropLayer";
import { OneWordCaption, OneWordCaptionConfig, CaptionWordInput, buildCaptionTokens } from "./components/OneWordCaption";
import { KeywordOverlayLayer, KeywordOverlayItem } from "./components/KeywordOverlayLayer";
import { MinimalOutroCta, MinimalOutroCtaConfig } from "./components/MinimalOutroCta";
import { SfxLayer, SfxConfig } from "./components/SfxLayer";
import { SafeZoneGuide } from "./components/SafeZoneGuide";
import type { BRollItem } from "./components/BRollLayer";

/* -------------------------------------------------------------
 * STYLE B — FULLBLEED SPEAKER (v5.0.0, ATM of fan clip page @dailyyskchaos)
 * Layers (bottom → top): speaker crop A-roll, full-screen B-roll, keyword
 * overlays, one-word caption, minimal YouTube CTA, SFX.
 * Spec: D:\Project\clonee\workflow.md §5
 * ------------------------------------------------------------- */

export type FullBleedClipProps = {
  style?: "fullbleed";
  videoSrc?: string;
  sourceWidth?: number;
  sourceHeight?: number;
  captions?: CaptionWordInput[];
  speakerCrop?: SpeakerCropSegment[];
  overlays?: KeywordOverlayItem[];
  brolls?: BRollItem[];
  caption?: OneWordCaptionConfig;
  outroCta?: MinimalOutroCtaConfig;
  sfx?: SfxConfig;
  showSafeZone?: boolean;
  durationInFrames?: number;
  fps?: number;
  width?: number;
  height?: number;
};

export const defaultFullBleedProps: FullBleedClipProps = {
  style: "fullbleed",
  videoSrc: "",
  sourceWidth: 1920,
  sourceHeight: 1080,
  captions: [],
  speakerCrop: [],
  overlays: [],
  brolls: [],
  caption: { enabled: true, centerY: 880, fontSize: 78 },
  outroCta: { enabled: true, channelName: "Lyrical Lemonade TV", durationInFrames: 75 },
  sfx: { enabled: true, auto: true, masterVolume: 0.25, minGapFrames: 8 },
  showSafeZone: false,
  durationInFrames: 1800,
  fps: 30,
  width: 1080,
  height: 1920,
};

const toPublic = (src: string) => {
  if (!src) return "";
  if (src.startsWith("http://") || src.startsWith("https://")) return src;
  const normalized = src.replace(/\\/g, "/");
  const isAbsolute = /^[a-zA-Z]:\//.test(normalized) || normalized.startsWith("/");
  const publicPath = normalized.includes("public/")
    ? normalized.split("public/").pop()!
    : isAbsolute
      ? normalized.split("/").pop()!
      : normalized;
  return staticFile(publicPath);
};

const FullscreenBRoll: React.FC<{ item: BRollItem }> = ({ item }) => {
  const src = toPublic(item.src);
  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {item.type === "image" ? (
        <Img src={src} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      ) : (
        <OffthreadVideo src={src} muted style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      )}
    </AbsoluteFill>
  );
};

export const calculateFullBleedMetadata: CalculateMetadataFunction<FullBleedClipProps> = ({ props }) => ({
  durationInFrames: props.durationInFrames || defaultFullBleedProps.durationInFrames!,
  fps: props.fps || defaultFullBleedProps.fps!,
  width: props.width || defaultFullBleedProps.width!,
  height: props.height || defaultFullBleedProps.height!,
  props,
});

export const FullBleedClipComponent: React.FC<FullBleedClipProps> = ({
  videoSrc = "",
  sourceWidth = 1920,
  sourceHeight = 1080,
  captions = [],
  speakerCrop = [],
  overlays = [],
  brolls = [],
  caption = defaultFullBleedProps.caption,
  outroCta = defaultFullBleedProps.outroCta!,
  sfx = defaultFullBleedProps.sfx,
  showSafeZone = false,
  durationInFrames = defaultFullBleedProps.durationInFrames!,
}) => {
  const { fps } = useVideoConfig();
  const ctaLength = outroCta.durationInFrames ?? 75;
  const ctaStart = Math.max(0, durationInFrames - ctaLength);
  const ctaEnabled = outroCta.enabled !== false;

  const tokens = React.useMemo(() => buildCaptionTokens(captions), [captions]);

  const sfxEvents = React.useMemo(
    () => ({
      durationInFrames,
      hookImpact: false,
      textMotion: [],
      brolls,
      htmlMotion: [],
      stickerFrames: overlays.filter((o) => !ctaEnabled || o.from < ctaStart).map((o) => o.from),
      outroEnabled: ctaEnabled,
      outroStartFrame: ctaStart,
    }),
    [durationInFrames, brolls, overlays, ctaEnabled, ctaStart],
  );

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      <SpeakerCropLayer
        src={toPublic(videoSrc)}
        segments={speakerCrop}
        sourceWidth={sourceWidth}
        sourceHeight={sourceHeight}
      />

      {brolls.map((b, i) => (
        <Sequence
          key={`${b.src}-${b.startFrame}-${i}`}
          name={`broll:${b.src.split("/").pop()}`}
          from={b.startFrame}
          durationInFrames={Math.max(1, b.endFrame - b.startFrame)}
          premountFor={fps}
        >
          <FullscreenBRoll item={b} />
        </Sequence>
      ))}

      <KeywordOverlayLayer overlays={overlays} hideFrom={ctaEnabled ? ctaStart : Infinity} />

      <OneWordCaption tokens={tokens} config={caption} />

      {ctaEnabled ? (
        <Sequence name="outro-cta" from={ctaStart} durationInFrames={ctaLength} premountFor={fps}>
          <MinimalOutroCta config={outroCta} />
        </Sequence>
      ) : null}

      <SfxLayer config={sfx} events={sfxEvents} />
      <SafeZoneGuide enabled={showSafeZone} />
    </AbsoluteFill>
  );
};

export const FullBleedComposition: React.FC = () => (
  <Composition
    id="FullBleedClip"
    component={FullBleedClipComponent}
    durationInFrames={defaultFullBleedProps.durationInFrames!}
    fps={defaultFullBleedProps.fps!}
    width={defaultFullBleedProps.width!}
    height={defaultFullBleedProps.height!}
    defaultProps={defaultFullBleedProps}
    calculateMetadata={calculateFullBleedMetadata}
  />
);
