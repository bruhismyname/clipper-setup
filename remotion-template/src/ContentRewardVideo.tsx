import React from "react";
import {
  AbsoluteFill,
  CalculateMetadataFunction,
  Composition,
  OffthreadVideo,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { BRollLayer, BRollItem } from "./components/BRollLayer";
import { HtmlMotionLayer, HtmlMotionItem } from "./components/HtmlMotionLayer";
import { TalkingHeadBadge, TalkingHeadConfig } from "./components/TalkingHeadLayer";
import { KineticTextMotion, KineticTextItem } from "./components/KineticTextMotion";
import {
  HookImpactFlash,
  useHookCameraSlam,
  AttentionTriggerBadge,
  HookAnimationConfig,
} from "./components/HookAnimations";
import {
  RetentionProgressBar,
  useAmbientCameraDrift,
  FloatingAmbientParticles,
  BodyAnimationConfig,
} from "./components/BodyAnimations";
import { DynamicCinematicVignette, ChromaticAberrationPulse, AnamorphicLightLeak, FilmGrainOverlayV2, AdvancedVisualEffectsConfig } from "./components/AdvancedVisualEffects";
import { SafeZoneGuide } from "./components/SafeZoneGuide";
import { EditorialGridBackground } from "./components/EditorialGridBackground";
import { TechnicalAnnotations } from "./components/TechnicalAnnotations";
import { SfxLayer, SfxConfig, defaultSfxConfig } from "./components/SfxLayer";

export type {
  BRollItem,
  HtmlMotionItem,
  TalkingHeadConfig,
  KineticTextItem,
  HookAnimationConfig,
  BodyAnimationConfig,
  AdvancedVisualEffectsConfig,
  SfxConfig,
};

export type CaptionWord = {
  text: string;
  start: number;
  end: number;
  startMs: number;
  endMs: number;
  startFrame: number;
  endFrame: number;
};

export type StickerItem = {
  text: string;
  subtext?: string;
  startFrame: number;
  endFrame: number;
  position?: "top-left" | "top-right" | "bottom-right" | "bottom-left";
  color?: string;
};

export type StatCallout = {
  targetNumber: number;
  prefix?: string;
  suffix?: string;
  label: string;
  startFrame: number;
  endFrame: number;
};

export type ContentRewardVideoProps = {
  videoSrc?: string;
  hookHeadline?: string;
  captions?: CaptionWord[];
  stickers?: StickerItem[];
  statCallout?: StatCallout;
  brolls?: BRollItem[];
  htmlMotion?: HtmlMotionItem[];
  talkingHead?: TalkingHeadConfig;
  textMotion?: KineticTextItem[];
  enableGrain?: boolean;
  hookAnimation?: HookAnimationConfig;
  bodyAnimation?: BodyAnimationConfig;
  advancedVisualEffects?: AdvancedVisualEffectsConfig;
  editorialGrid?: boolean;
  technicalAnnotations?: boolean;
  docTag?: string;
  showSafeZone?: boolean;
  sfx?: SfxConfig;
  outroCta?: {
    enabled?: boolean;
    channelName?: string;
    seriesName?: string;
    ctaText?: string;
  };
  durationInFrames?: number;
  fps?: number;
  width?: number;
  height?: number;
};

export const defaultRewardProps: ContentRewardVideoProps = {
  videoSrc: "c02-clip.mp4",
  hookHeadline: "WHO HAS HURT WOMEN MORE?!",
  durationInFrames: 864,
  fps: 30,
  width: 1080,
  height: 1920,
  enableGrain: true,
  showSafeZone: false,
  editorialGrid: true,
  technicalAnnotations: true,
  docTag: "ARCHIVE // VIRAL DOSSIER",
  hookAnimation: {
    enabled: true,
    impactFlash: true,
    cameraSlam: true,
    attentionBadge: {
      text: "🔥 MUST WATCH",
      color: "#FF3B30",
    },
  },
  bodyAnimation: {
    enabled: true,
    retentionProgressBar: true,
    ambientCameraDrift: true,
    floatingParticles: true,
  },
  advancedVisualEffects: {
    enabled: true,
    vignette: true,
    chromaticAberration: true,
    lightLeak: true,
    filmGrain: true,
  },
  stickers: [],
  statCallout: undefined,
  captions: [],
  brolls: [],
  htmlMotion: [],
  talkingHead: undefined,
  textMotion: [],
  sfx: defaultSfxConfig,
};

/* -------------------------------------------------------------
 * 1. PAPERCLIP STICKER BADGE (Universal Safe Zone Anchored)
 * ------------------------------------------------------------- */
export const PaperclipSticker: React.FC<{
  sticker: StickerItem;
  currentFrame: number;
  fps: number;
}> = ({ sticker, currentFrame, fps }) => {
  if (currentFrame < sticker.startFrame || currentFrame > sticker.endFrame) {
    return null;
  }

  const age = currentFrame - sticker.startFrame;
  const enterSpring = spring({
    frame: age,
    fps,
    config: {
      damping: 10,
      stiffness: 150,
      mass: 0.8,
    },
  });

  const scale = interpolate(enterSpring, [0, 1], [0.3, 1]);
  const opacity = interpolate(age, [0, 5], [0, 1], {
    extrapolateRight: "clamp",
  });

  const remaining = sticker.endFrame - currentFrame;
  const exitOpacity = interpolate(remaining, [0, 8], [0, 1], {
    extrapolateLeft: "clamp",
  });

  const finalOpacity = Math.min(opacity, exitOpacity);

  // Position anchored inside 860px safe zone (left/right margin 110px)
  const posStyle: React.CSSProperties =
    sticker.position === "top-left"
      ? { top: 505, left: 110, transform: `scale(${scale}) rotate(-4deg)` }
      : sticker.position === "bottom-left"
      ? { top: 1160, left: 110, transform: `scale(${scale}) rotate(-3deg)` }
      : sticker.position === "bottom-right"
      ? { top: 1160, right: 110, transform: `scale(${scale}) rotate(4deg)` }
      : { top: 505, right: 110, transform: `scale(${scale}) rotate(3deg)` };

  const badgeColor = sticker.color || "#FF3B30";

  return (
    <div
      style={{
        position: "absolute",
        zIndex: 50,
        opacity: finalOpacity,
        transformOrigin: "center center",
        ...posStyle,
      }}
    >
      <div
        style={{
          backgroundColor: "#FFFFFF",
          color: "#0F172A",
          border: "8px solid #FFFFFF",
          borderRadius: 22,
          padding: "12px 24px",
          boxShadow: "0 20px 45px rgba(0,0,0,0.7), 0 4px 12px rgba(0,0,0,0.3)",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 4,
        }}
      >
        {sticker.subtext && (
          <span
            style={{
              backgroundColor: badgeColor,
              color: "#FFFFFF",
              fontSize: 15,
              fontWeight: 900,
              padding: "4px 12px",
              borderRadius: 8,
              letterSpacing: "1px",
              textTransform: "uppercase",
            }}
          >
            {sticker.subtext}
          </span>
        )}
        <span
          style={{
            fontSize: 26,
            fontWeight: 900,
            letterSpacing: "-0.5px",
            textTransform: "uppercase",
            color: "#0F172A",
            whiteSpace: "nowrap",
          }}
        >
          {sticker.text}
        </span>
      </div>
    </div>
  );
};

/* -------------------------------------------------------------
 * 1.5 OUTRO CALL-TO-ACTION (CTA) BANNER (Campaign Compliance Rule 4)
 * ------------------------------------------------------------- */
export const OutroCtaBanner: React.FC<{
  currentFrame: number;
  totalFrames: number;
  fps: number;
  channelName?: string;
  seriesName?: string;
  ctaText?: string;
}> = ({
  currentFrame,
  totalFrames,
  fps,
  channelName = "LYRICAL LEMONADE TV",
  seriesName = "NO COMFORT",
  ctaText = "WATCH FULL EPISODE ON YOUTUBE",
}) => {
  const triggerFrame = Math.max(0, totalFrames - 90); // last 3 seconds
  if (currentFrame < triggerFrame) return null;

  const age = currentFrame - triggerFrame;
  const enterSpring = spring({
    frame: age,
    fps,
    config: { damping: 11, stiffness: 140, mass: 0.9 },
  });

  const scale = interpolate(enterSpring, [0, 1], [0.82, 1]);
  const opacity = interpolate(age, [0, 6], [0, 1], { extrapolateRight: "clamp" });

  return (
    <div
      style={{
        position: "absolute",
        top: 660,
        left: 110,
        right: 110,
        zIndex: 85,
        opacity,
        transform: `scale(${scale})`,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: 840,
          background: "linear-gradient(135deg, rgba(15, 23, 42, 0.96) 0%, rgba(2, 6, 23, 0.98) 100%)",
          border: "3px solid #FF3B30",
          borderRadius: 26,
          padding: "26px 32px",
          boxShadow: "0 25px 60px rgba(0, 0, 0, 0.85), 0 0 35px rgba(255, 59, 48, 0.45)",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 12,
          backdropFilter: "blur(20px)",
        }}
      >
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            backgroundColor: "#FF0000",
            color: "#FFFFFF",
            padding: "8px 20px",
            borderRadius: 12,
            fontSize: 18,
            fontWeight: 900,
            letterSpacing: "1.5px",
            textTransform: "uppercase",
            boxShadow: "0 4px 18px rgba(255, 0, 0, 0.6)",
          }}
        >
          <span>▶ YOUTUBE</span>
        </div>
        <div
          style={{
            fontSize: 34,
            fontWeight: 900,
            color: "#FFFFFF",
            textAlign: "center",
            textTransform: "uppercase",
            letterSpacing: "-0.5px",
            lineHeight: 1.25,
          }}
        >
          {ctaText}
        </div>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            fontSize: 22,
            fontWeight: 800,
            color: "#FFE600",
            letterSpacing: "1px",
            textTransform: "uppercase",
          }}
        >
          <span>{channelName}</span>
          <span style={{ color: "#64748B" }}>•</span>
          <span style={{ color: "#94A3B8" }}>{seriesName}</span>
        </div>
      </div>
    </div>
  );
};

/* -------------------------------------------------------------
 * 2. AUDIO VISUALIZER BARS (Kinetic Audio Energy)
 * ------------------------------------------------------------- */
export const AudioEqualizerBars: React.FC<{ frame: number }> = ({ frame }) => {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "flex-end",
        gap: 6,
        height: 26,
        padding: "0 8px",
      }}
    >
      {[0.4, 0.8, 0.5, 0.9, 0.6, 0.7].map((speed, i) => {
        const h = Math.abs(Math.sin((frame * 0.25 + i * 1.5) * speed)) * 20 + 6;
        return (
          <div
            key={i}
            style={{
              width: 5,
              height: h,
              backgroundColor: i % 2 === 0 ? "#FFE600" : "#FF3B30",
              borderRadius: 3,
              boxShadow: "0 0 10px rgba(255, 230, 0, 0.5)",
            }}
          />
        );
      })}
    </div>
  );
};

/* -------------------------------------------------------------
 * 3. KEYWORD CONFIGS & POPUP BADGE
 * ------------------------------------------------------------- */
const KEYWORD_CONFIGS: Record<
  string,
  { label: string; tag: string; emoji: string; color: string }
> = {
  SYDNEY: { label: "SYDNEY SWEENEY", tag: "HOLLYWOOD STAR", emoji: "⭐", color: "#FF2A6D" },
  SIDNEY: { label: "SYDNEY SWEENEY", tag: "HOLLYWOOD STAR", emoji: "⭐", color: "#FF2A6D" },
  SWEENEY: { label: "SYDNEY SWEENEY", tag: "HOLLYWOOD STAR", emoji: "⭐", color: "#FF2A6D" },
  LINDSAY: { label: "LINDSAY CLANCY", tag: "THE VIRAL CASE", emoji: "⚖️", color: "#05D9E8" },
  LINDSEY: { label: "LINDSAY CLANCY", tag: "THE VIRAL CASE", emoji: "⚖️", color: "#05D9E8" },
  CLANCY: { label: "LINDSAY CLANCY", tag: "THE VIRAL CASE", emoji: "⚖️", color: "#05D9E8" },
  HURT: { label: "HURT WOMEN MORE", tag: "THE CORE DEBATE", emoji: "💥", color: "#FF3B30" },
  WOMEN: { label: "WHO HURT WOMEN?", tag: "PUBLIC PERCEPTION", emoji: "⚡", color: "#FFE600" },
  MORE: { label: "WHO DID MORE HARM?", tag: "SHOCKING COMPARISON", emoji: "🔥", color: "#FF5722" },
  PHONE: { label: "WATCHING ON PHONE", tag: "STREET CHALLENGE", emoji: "📱", color: "#00E676" },
  IMAGE: { label: "PHOTO COMPARISON", tag: "LOOK CLOSELY", emoji: "🖼️", color: "#00B0FF" },
  POINTED: { label: "SHE POINTED TO SYDNEY!", tag: "UNBELIEVABLE PICK", emoji: "👉", color: "#FF9100" },
  PEOPLE: { label: "TWO FAMOUS PEOPLE", tag: "CAN YOU GUESS?", emoji: "👥", color: "#7928CA" },
  TWO: { label: "WHICH ONE?", tag: "SIDE BY SIDE", emoji: "👀", color: "#7928CA" },
  KNOWN: { label: "WHAT ARE THEY KNOWN FOR?", tag: "THE QUESTION", emoji: "❓", color: "#00E5FF" },
  CRAZY: { label: "HOW CRAZY IS THIS?!", tag: "UNREAL SITUATION", emoji: "🤯", color: "#FF3B30" },
  PROPAGANDA: { label: "ONLINE PROPAGANDA", tag: "MASS MISINFORMATION", emoji: "📢", color: "#FF9100" },
  ONLINE: { label: "VIRAL ON THE INTERNET", tag: "SOCIAL MEDIA BUZZ", emoji: "🌐", color: "#00E5FF" },
  TRIAL: { label: "THE MURDER TRIAL", tag: "HIGH STAKES CASE", emoji: "⚖️", color: "#FF2A6D" },
  PATRICK: { label: "PATRICK CLANCY", tag: "THE HUSBAND", emoji: "👤", color: "#05D9E8" },
  KILLED: { label: "WHAT ACTUALLY HAPPENED?", tag: "THE TRAGEDY", emoji: "⚠️", color: "#FF3B30" },
  KIDS: { label: "THE THREE CHILDREN", tag: "HEARTBREAKING CASE", emoji: "💔", color: "#FF1744" },
  FUCKED: { label: "SOCIETY IS DOOMED", tag: "TOTAL DISBELIEF", emoji: "💀", color: "#FF3B30" },
  KIDDING: { label: "ARE YOU KIDDING ME?!", tag: "SHOCK FACTOR", emoji: "🤦", color: "#FFE600" },
  BELIEVE: { label: "CANNOT BELIEVE THIS", tag: "PURE DISBELIEF", emoji: "👀", color: "#00E676" },
  SEEING: { label: "LOOK AT THE COMMENTS", tag: "PUBLIC CONFUSION", emoji: "📱", color: "#7928CA" },
  REACTIONS: { label: "VIRAL REACTIONS", tag: "PODCAST COMMENTARY", emoji: "🔥", color: "#FF5722" },
  NEVER: { label: "NEVER SEEN BEFORE", tag: "HISTORIC DELUSION", emoji: "🚫", color: "#E040FB" },
  NARCISSISM: { label: "NARCISSISM DEFINED", tag: "PSYCHOLOGY", emoji: "🪞", color: "#FF3B30" },
  WNBA: { label: "WNBA BASKETBALL", tag: "PRO SPORTS", emoji: "🏀", color: "#FF9100" },
  OLYMPIC: { label: "OLYMPIC SPRINTER", tag: "ATHLETICS", emoji: "🥇", color: "#FFE600" },
  SPRINTER: { label: "OLYMPIC SPRINTER", tag: "ATHLETICS", emoji: "🏃‍♀️", color: "#FFE600" },
  ATHLETE: { label: "FEMALE ATHLETE", tag: "THE DEBATE", emoji: "⚡", color: "#05D9E8" },
  ATHLETES: { label: "FEMALE ATHLETES", tag: "THE DEBATE", emoji: "⚡", color: "#05D9E8" },
  UNIFORMS: { label: "OFFICIAL UNIFORMS", tag: "COMPETITION", emoji: "🎽", color: "#00E676" },
  COMPETE: { label: "HOW THEY COMPETE", tag: "REAL SPORTS", emoji: "🏆", color: "#00E5FF" },
  NAKED: { label: "NOT COMPETING NAKED", tag: "THE PUNCHLINE", emoji: "👀", color: "#FF2A6D" },
};

export const KeywordPopupBadge: React.FC<{
  cleanWord: string;
  frame: number;
  fps: number;
  startFrame: number;
}> = ({ cleanWord, frame, fps, startFrame }) => {
  const cfg = KEYWORD_CONFIGS[cleanWord];
  if (!cfg) return null;

  const age = frame - startFrame;
  const enterSpring = spring({
    frame: age,
    fps,
    config: { damping: 9, stiffness: 180, mass: 0.7 },
  });

  const scale = interpolate(enterSpring, [0, 1], [0.4, 1.05]);
  const enterOpacity = interpolate(age, [0, 4], [0, 1], { extrapolateRight: "clamp" });
  const exitOpacity = interpolate(age, [22, 28], [1, 0], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const opacity = Math.min(enterOpacity, exitOpacity);

  return (
    <div
      style={{
        position: "absolute",
        top: 1210,
        left: "50%",
        transform: `translateX(-50%) scale(${scale})`,
        opacity,
        zIndex: 55,
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 14,
          backgroundColor: "#0B0F19",
          border: `3px solid ${cfg.color}`,
          borderRadius: 28,
          padding: "10px 24px",
          boxShadow: `0 16px 36px rgba(0,0,0,0.85), 0 0 30px ${cfg.color}66`,
          maxWidth: 820,
        }}
      >
        <span style={{ fontSize: 32 }}>{cfg.emoji}</span>
        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-start" }}>
          <span
            style={{
              fontSize: 13,
              fontWeight: 900,
              color: cfg.color,
              letterSpacing: "1.2px",
              textTransform: "uppercase",
            }}
          >
            {cfg.tag}
          </span>
          <span
            style={{
              fontSize: 22,
              fontWeight: 900,
              color: "#FFFFFF",
              letterSpacing: "-0.5px",
              textTransform: "uppercase",
              whiteSpace: "nowrap",
            }}
          >
            {cfg.label}
          </span>
        </div>
      </div>
    </div>
  );
};

/* -------------------------------------------------------------
 * 4. ANIMATED STAT COUNTER CARD
 * ------------------------------------------------------------- */
export const StatCounterCard: React.FC<{
  stat: StatCallout;
  currentFrame: number;
  fps: number;
}> = ({ stat, currentFrame, fps }) => {
  if (currentFrame < stat.startFrame || currentFrame > stat.endFrame) {
    return null;
  }

  const age = currentFrame - stat.startFrame;
  const enterSpring = spring({
    frame: age,
    fps,
    config: { damping: 11, stiffness: 120 },
  });

  const scale = interpolate(enterSpring, [0, 1], [0.7, 1]);
  const opacity = interpolate(age, [0, 6], [0, 1], { extrapolateRight: "clamp" });

  const countProgress = interpolate(age, [0, 24], [0, 1], { extrapolateRight: "clamp" });
  const displayNum = Math.round(countProgress * stat.targetNumber);

  return (
    <div
      style={{
        position: "absolute",
        top: 1150,
        left: "50%",
        transform: `translateX(-50%) scale(${scale})`,
        zIndex: 55,
        opacity,
      }}
    >
      <div
        style={{
          background: "rgba(15, 23, 42, 0.94)",
          backdropFilter: "blur(12px)",
          border: "3px solid #FFE600",
          borderRadius: 24,
          padding: "16px 36px",
          boxShadow: "0 25px 50px rgba(0,0,0,0.8), 0 0 30px rgba(255, 230, 0, 0.3)",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 4,
          maxWidth: 820,
        }}
      >
        <div
          style={{
            fontSize: 52,
            fontWeight: 900,
            color: "#FFE600",
            letterSpacing: "-1px",
            lineHeight: 1.1,
            fontVariantNumeric: "tabular-nums",
          }}
        >
          {stat.prefix || ""}
          {displayNum}
          {stat.suffix || ""}
        </div>
        <div
          style={{
            fontSize: 19,
            fontWeight: 800,
            color: "#FFFFFF",
            letterSpacing: "1.5px",
            textTransform: "uppercase",
            opacity: 0.9,
          }}
        >
          {stat.label}
        </div>
      </div>
    </div>
  );
};

/* -------------------------------------------------------------
 * 5. METADATA CALCULATION
 * ------------------------------------------------------------- */
export const calculateRewardMetadata: CalculateMetadataFunction<ContentRewardVideoProps> = ({ props }) => {
  return {
    durationInFrames: props.durationInFrames || defaultRewardProps.durationInFrames,
    fps: props.fps || defaultRewardProps.fps,
    width: props.width || defaultRewardProps.width,
    height: props.height || defaultRewardProps.height,
    props: {
      ...props,
    },
  };
};

/* -------------------------------------------------------------
 * 6. MAIN COMPONENT (v4.0.0 Universal Safe Zone & Advanced Stack)
 * ------------------------------------------------------------- */
export const ContentRewardVideoComponent: React.FC<ContentRewardVideoProps> = ({
  videoSrc,
  hookHeadline = defaultRewardProps.hookHeadline,
  captions = [],
  stickers = [],
  statCallout,
  brolls = [],
  htmlMotion = [],
  talkingHead,
  textMotion = [],
  enableGrain = true,
  hookAnimation = defaultRewardProps.hookAnimation,
  bodyAnimation = defaultRewardProps.bodyAnimation,
  advancedVisualEffects = defaultRewardProps.advancedVisualEffects,
  editorialGrid = defaultRewardProps.editorialGrid,
  technicalAnnotations = defaultRewardProps.technicalAnnotations,
  docTag = defaultRewardProps.docTag,
  showSafeZone = false,
  sfx = defaultRewardProps.sfx,
  outroCta = {
    enabled: true,
    channelName: "LYRICAL LEMONADE TV",
    seriesName: "NO COMFORT",
    ctaText: "WATCH FULL EPISODE ON YOUTUBE",
  },
  durationInFrames = defaultRewardProps.durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const resolvedVideoSrc = React.useMemo(() => {
    if (!videoSrc) return "";
    if (videoSrc.startsWith("http://") || videoSrc.startsWith("https://")) {
      return videoSrc;
    }
    const baseName = videoSrc.replace(/\\/g, "/").split("/").pop() || videoSrc;
    try {
      return staticFile(baseName);
    } catch {
      return baseName;
    }
  }, [videoSrc]);

  // Hook Camera Slam & Shake (Frames 0 to 18)
  const isHookSlamActive = hookAnimation?.cameraSlam !== false;
  const hookSlam = useHookCameraSlam(frame, fps, isHookSlamActive);

  // Body Ambient Camera Drift (Continuous breathing motion)
  const isDriftActive = bodyAnimation?.ambientCameraDrift !== false;
  const { driftScale, driftX, driftY } = useAmbientCameraDrift(frame, isDriftActive);

  // Hook Headline animation (elastic pop)
  const headlineSpring = spring({
    frame,
    fps,
    config: {
      damping: 10,
      stiffness: 140,
      mass: 0.9,
    },
  });

  const headlineScale = interpolate(headlineSpring, [0, 1], [0.75, 1]);
  const headlineOpacity = interpolate(frame, [0, 6], [0, 1], {
    extrapolateRight: "clamp",
  });

  // Active word captions (with anti-flicker smoothing)
  let activeWordIndex = captions.findIndex(
    (w) => frame >= w.startFrame && frame <= w.endFrame
  );
  if (activeWordIndex === -1) {
    activeWordIndex = captions.findIndex(
      (w) => frame > w.endFrame && frame <= w.endFrame + 5
    );
  }

  let visibleWords: { word: CaptionWord; isActive: boolean; isKey: boolean }[] = [];
  if (activeWordIndex !== -1) {
    const startIdx = Math.max(0, activeWordIndex - 1);
    const endIdx = Math.min(captions.length, activeWordIndex + 2);
    visibleWords = captions.slice(startIdx, endIdx).map((w, idx) => {
      const isAct = startIdx + idx === activeWordIndex;
      const cleanW = w.text.toUpperCase().replace(/[^A-Z]/g, "");
      const isKey = KEYWORD_CONFIGS[cleanW] !== undefined;
      return {
        word: w,
        isActive: isAct,
        isKey,
      };
    });
  }

  // Active Keyword Popup Badge (persists for 28 frames ~ 0.93 seconds)
  const KEYWORD_DURATION = 28;
  let currentKeyWord = "";
  let activeWordStartFrame = 0;
  for (let i = captions.length - 1; i >= 0; i--) {
    const w = captions[i];
    const cleanW = w.text.toUpperCase().replace(/[^A-Z]/g, "");
    if (KEYWORD_CONFIGS[cleanW] && frame >= w.startFrame && frame <= w.startFrame + KEYWORD_DURATION) {
      currentKeyWord = cleanW;
      activeWordStartFrame = w.startFrame;
      break;
    }
  }

  // Determine trigger frames for Chromatic Aberration (Hook start + Text Slams)
  const chromaticTriggerFrames = React.useMemo(() => {
    const triggers = [0];
    if (textMotion) {
      textMotion.forEach((tm) => triggers.push(tm.startFrame));
    }
    return triggers;
  }, [textMotion]);

  // Determine B-Roll entrance frame for Anamorphic Light Leak
  const lightLeakStartFrame = React.useMemo(() => {
    if (brolls && brolls.length > 0) return brolls[0].startFrame;
    if (htmlMotion && htmlMotion.length > 0) return htmlMotion[0].startFrame;
    return 0;
  }, [brolls, htmlMotion]);

  const sfxEvents = React.useMemo(
    () => ({
      durationInFrames: durationInFrames || defaultRewardProps.durationInFrames!,
      hookImpact: hookAnimation?.enabled !== false && hookAnimation?.impactFlash !== false,
      textMotion,
      brolls,
      htmlMotion,
      stickerFrames: stickers.map((st) => st.startFrame),
      statFrame: statCallout?.startFrame,
      outroEnabled: outroCta?.enabled !== false,
    }),
    [durationInFrames, hookAnimation, textMotion, brolls, htmlMotion, stickers, statCallout, outroCta]
  );

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#050505",
        fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
      }}
    >
      {/* 0. LAYER BACKGROUND BLUR */}
      {resolvedVideoSrc ? (
        <AbsoluteFill style={{ overflow: "hidden" }}>
          <OffthreadVideo
            src={resolvedVideoSrc}
            muted
            style={{
              width: "100%",
              height: "100%",
              objectFit: "cover",
              filter: "blur(48px) brightness(0.28) saturate(1.2)",
              transform: "scale(1.35)",
            }}
          />
        </AbsoluteFill>
      ) : (
        <AbsoluteFill
          style={{
            background: "linear-gradient(180deg, #0f172a 0%, #020617 100%)",
          }}
        />
      )}

      {/* 0.5 EDITORIAL GRID WALLPAPER (Gozmotion / Usman Explains Minimal Blueprint) */}
      <EditorialGridBackground enabled={editorialGrid} opacity={0.25} />

      {/* 1. BODY ANIMATION: FLOATING AMBIENT PARTICLES (Bokeh Depth) */}
      {bodyAnimation?.floatingParticles !== false && (
        <FloatingAmbientParticles frame={frame} count={16} />
      )}

      {/* 1.5 TECHNICAL ANNOTATIONS (Gozmotion Viewfinder Brackets & Dossier Tags) */}
      <TechnicalAnnotations enabled={technicalAnnotations} docTag={docTag} />

      {/* 2. LAYER MAIN VIDEO (16:9 CENTERED A-ROLL WITH UNIVERSAL 860px SAFE WIDTH) */}
      {(() => {
        const aRollZoom = talkingHead?.dynamicPunchZoom !== false && currentKeyWord ? 1.05 : 1.0;
        const totalScale = aRollZoom * hookSlam.scale * driftScale;
        const totalX = hookSlam.offsetX + driftX;
        const totalY = hookSlam.offsetY + driftY;

        return (
          <div
            style={{
              position: "absolute",
              top: "47%",
              left: "50%",
              transform: `translate(calc(-50% + ${totalX}px), calc(-50% + ${totalY}px)) scale(${totalScale})`,
              width: 860,
              aspectRatio: "16 / 9",
              borderRadius: 24,
              overflow: "hidden",
              boxShadow: "0 32px 85px rgba(0, 0, 0, 0.95), 0 0 0 2px rgba(255, 255, 255, 0.14)",
              backgroundColor: "#111111",
              transition: "transform 0.12s ease-out",
            }}
          >
            {resolvedVideoSrc ? (
              <OffthreadVideo
                src={resolvedVideoSrc}
                style={{
                  width: "100%",
                  height: "100%",
                  objectFit: "cover",
                }}
              />
            ) : (
              <div
                style={{
                  width: "100%",
                  height: "100%",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  color: "#aaaaaa",
                  fontSize: 26,
                  fontWeight: 600,
                }}
              >
                Video Source Belum Terisi
              </div>
            )}
          </div>
        );
      })()}

      {/* 3. BODY ANIMATION: RETENTION SCRUBBER PROGRESS BAR (Directly below A-Roll card) */}
      {bodyAnimation?.retentionProgressBar !== false && (
        <RetentionProgressBar
          currentFrame={frame}
          durationInFrames={durationInFrames || defaultRewardProps.durationInFrames!}
          width={860}
          top="calc(47% + 252px)"
        />
      )}

      {/* 4. LAYER B-ROLL CUTAWAYS (Editorial Card inside 840px Safe Width) */}
      <BRollLayer brolls={brolls} />

      {/* 5. LAYER HTML MOTION MOCKUPS (Browser, Tweet, Search within 840px Safe Width) */}
      <HtmlMotionLayer items={htmlMotion} />

      {/* 6. LAYER TALKING HEAD BADGE (Speaker Spotlight inside Safe Margins) */}
      <TalkingHeadBadge config={talkingHead} frame={frame} fps={fps} />

      {/* 7. HOOK ANIMATION: ATTENTION TRIGGER BADGE (Detik 0 - 3) */}
      {hookAnimation?.attentionBadge && (
        <AttentionTriggerBadge
          badge={hookAnimation.attentionBadge}
          frame={frame}
          fps={fps}
        />
      )}

      {/* 8. LAYER HOOK HEADLINE BANNER (Top Safe Zone Y=355, MaxWidth 820px, Clear of Search Bar) */}
      {hookHeadline && (
        <div
          style={{
            position: "absolute",
            top: 355,
            left: "50%",
            transform: `translateX(-50%) scale(${headlineScale})`,
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            opacity: headlineOpacity,
            zIndex: 48,
            width: "100%",
            pointerEvents: "none",
          }}
        >
          <div
            style={{
              backgroundColor: "#FFE600",
              color: "#000000",
              padding: "16px 32px",
              borderRadius: 22,
              fontWeight: 900,
              fontSize: 40,
              textAlign: "center",
              textTransform: "uppercase",
              letterSpacing: "-0.5px",
              boxShadow: "0 18px 45px rgba(0, 0, 0, 0.75), 0 2px 6px rgba(0,0,0,0.3)",
              lineHeight: 1.25,
              maxWidth: 820,
              display: "flex",
              alignItems: "center",
              gap: 14,
            }}
          >
            <span>{hookHeadline}</span>
            <AudioEqualizerBars frame={frame} />
          </div>
        </div>
      )}

      {/* 9. MG-STYLES: PAPERCLIP STICKERS (Anchored inside Safe Margins) */}
      {stickers.map((st, i) => (
        <PaperclipSticker
          key={`${st.text}-${i}`}
          sticker={st}
          currentFrame={frame}
          fps={fps}
        />
      ))}

      {/* 10. MG-STYLES: KEYWORD POPUP BADGE (Golden Reading Band) */}
      {currentKeyWord && (
        <KeywordPopupBadge
          cleanWord={currentKeyWord}
          frame={frame}
          fps={fps}
          startFrame={activeWordStartFrame}
        />
      )}

      {/* 11. MG-STYLES: STAT COUNTER CARD */}
      {statCallout && (
        <StatCounterCard stat={statCallout} currentFrame={frame} fps={fps} />
      )}

      {/* 12. LAYER KINETIC TEXT MOTION (Slam Typography inside Safe Width) */}
      <KineticTextMotion items={textMotion} />

      {/* 13. KINETIC HIGHLIGHT CAPTIONS (Hormozi / MrBeast Boxed Pop Inside Safe Zone) */}
      <div
        style={{
          position: "absolute",
          top: 1350,
          left: 110,
          right: 110,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          flexWrap: "wrap",
          gap: 14,
          minHeight: 120,
          zIndex: 45,
          pointerEvents: "none",
        }}
      >
        {visibleWords.map(({ word, isActive, isKey }, i) => {
          if (isActive) {
            const wordAge = frame - word.startFrame;
            const popSpring = spring({
              frame: wordAge,
              fps,
              config: { damping: 9, stiffness: 200, mass: 0.6 },
            });
            const wordScale = interpolate(popSpring, [0, 1], [0.85, isKey ? 1.2 : 1.1]);

            return (
              <div
                key={`${word.startFrame}-${i}`}
                style={{
                  transform: `scale(${wordScale})`,
                  backgroundColor: isKey ? "#FF3B30" : "#FFE600",
                  color: isKey ? "#FFFFFF" : "#000000",
                  padding: "8px 20px",
                  borderRadius: 18,
                  fontSize: 50,
                  fontWeight: 900,
                  boxShadow: isKey
                    ? "0 8px 30px rgba(255, 59, 48, 0.8), 0 2px 8px #000000"
                    : "0 8px 25px rgba(255, 230, 0, 0.7), 0 2px 8px #000000",
                  letterSpacing: "0.5px",
                  textTransform: "uppercase",
                  transition: "transform 0.03s ease-out",
                }}
              >
                {word.text}
              </div>
            );
          }

          return (
            <span
              key={`${word.startFrame}-${i}`}
              style={{
                fontSize: 44,
                fontWeight: 900,
                color: "#FFFFFF",
                textShadow: "0 4px 18px rgba(0, 0, 0, 0.95)",
                textTransform: "uppercase",
                letterSpacing: "0.5px",
                padding: "8px 10px",
                opacity: 0.85,
              }}
            >
              {word.text}
            </span>
          );
        })}
      </div>

      {/* 13.5 OUTRO CALL-TO-ACTION (CTA) BANNER (Campaign Rule 4) */}
      {outroCta?.enabled !== false && (
        <OutroCtaBanner
          currentFrame={frame}
          totalFrames={durationInFrames || defaultRewardProps.durationInFrames!}
          fps={fps}
          channelName={outroCta?.channelName}
          seriesName={outroCta?.seriesName}
          ctaText={outroCta?.ctaText}
        />
      )}

      {/* 14. ADVANCED VISUAL EFFECT: DYNAMIC CINEMATIC VIGNETTE */}
      {advancedVisualEffects?.vignette !== false && (
        <DynamicCinematicVignette intensity={0.72} />
      )}

      {/* 15. ADVANCED VISUAL EFFECT: ANAMORPHIC LIGHT LEAK SWEEP */}
      {advancedVisualEffects?.lightLeak !== false && (
        <AnamorphicLightLeak
          frame={frame}
          startFrame={lightLeakStartFrame}
          duration={35}
        />
      )}

      {/* 16. ADVANCED VISUAL EFFECT: CHROMATIC ABERRATION PULSE */}
      {advancedVisualEffects?.chromaticAberration !== false && (
        <ChromaticAberrationPulse
          frame={frame}
          triggerFrames={chromaticTriggerFrames}
        />
      )}

      {/* AUDIO: AUTO-CUED SFX (CC0 library in public/sfx) */}
      <SfxLayer config={sfx} events={sfxEvents} />

      {/* 17. HOOK ANIMATION: IMPACT FLASH (Detik 0.0 - 0.2) */}
      {hookAnimation?.impactFlash !== false && <HookImpactFlash frame={frame} />}

      {/* 18. ADVANCED VISUAL EFFECT: MULTI-OCTAVE 35mm FILM GRAIN (Anti-AI Slop) */}
      {enableGrain && advancedVisualEffects?.filmGrain !== false && (
        <FilmGrainOverlayV2 opacity={0.08} />
      )}

      {/* 19. OPTIONAL: SAFE ZONE GUIDE (Overlay for dev/layout debugging) */}
      <SafeZoneGuide enabled={showSafeZone} />
    </AbsoluteFill>
  );
};

export const ContentRewardComposition: React.FC = () => {
  return (
    <Composition
      id="ContentRewardVideo"
      component={ContentRewardVideoComponent}
      durationInFrames={defaultRewardProps.durationInFrames!}
      fps={defaultRewardProps.fps!}
      width={defaultRewardProps.width!}
      height={defaultRewardProps.height!}
      defaultProps={defaultRewardProps}
      calculateMetadata={calculateRewardMetadata}
    />
  );
};
