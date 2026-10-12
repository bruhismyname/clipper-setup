import React from "react";
import { staticFile } from "remotion";
import { Audio } from "@remotion/media";
import sfxLibrary from "../sfx-library.json";
import type { BRollItem } from "./BRollLayer";
import type { HtmlMotionItem } from "./HtmlMotionLayer";
import type { KineticTextItem } from "./KineticTextMotion";

/* -------------------------------------------------------------
 * SFX LAYER (CC0 library in public/sfx, built by hook-radar/scripts/sfx_fetch.py)
 * Auto-cues sound effects on the timeline events the visuals already define,
 * so every hook, slam, cutaway and CTA lands with a sound without manual placement.
 * ------------------------------------------------------------- */

export type SfxCategory =
  | "impact"
  | "hit"
  | "whoosh"
  | "swipe"
  | "pop"
  | "riser"
  | "ding"
  | "glitch"
  | "record-scratch"
  | "shutter";

export type SfxCue = {
  frame: number;
  category: SfxCategory;
  /** 1-based variant index; defaults to rotating through the library */
  variant?: number;
  /** Relative to masterVolume (0-1.5) */
  volume?: number;
};

export type SfxConfig = {
  enabled?: boolean;
  /** Derive cues from hook, text slams, B-roll, mockups, stickers and the outro CTA */
  auto?: boolean;
  /** Overall SFX loudness; keep low so the speaker stays dominant */
  masterVolume?: number;
  /** Extra hand-placed cues, merged with the auto cues */
  cues?: SfxCue[];
  /** Cues closer than this to the previous one are dropped so sounds never pile up */
  minGapFrames?: number;
};

export const defaultSfxConfig: Required<Omit<SfxConfig, "cues">> = {
  enabled: true,
  auto: true,
  masterVolume: 0.35,
  minGapFrames: 8,
};

const library = sfxLibrary as Partial<Record<SfxCategory, string[]>>;

type TimelineEvents = {
  durationInFrames: number;
  hookImpact: boolean;
  textMotion: KineticTextItem[];
  brolls: BRollItem[];
  htmlMotion: HtmlMotionItem[];
  stickerFrames: number[];
  statFrame?: number;
  outroEnabled: boolean;
  /** Frame where the outro CTA appears; defaults to the last 90 frames (OutroCtaBanner) */
  outroStartFrame?: number;
};

export const buildAutoSfxCues = (ev: TimelineEvents): SfxCue[] => {
  const cues: SfxCue[] = [];
  if (ev.hookImpact) cues.push({ frame: 0, category: "impact", volume: 1 });
  ev.textMotion.forEach((tm) =>
    cues.push({ frame: tm.startFrame, category: tm.type === "glitch" ? "glitch" : "hit", volume: 0.9 })
  );
  ev.brolls.forEach((b) => cues.push({ frame: b.startFrame, category: "whoosh", volume: 0.8 }));
  ev.htmlMotion.forEach((h) =>
    cues.push({ frame: h.startFrame, category: h.type === "notification" ? "pop" : "whoosh", volume: 0.8 })
  );
  ev.stickerFrames.forEach((f) => cues.push({ frame: f, category: "pop", volume: 0.6 }));
  if (ev.statFrame !== undefined) cues.push({ frame: ev.statFrame, category: "pop", volume: 0.7 });
  // Same trigger as the outro CTA (OutroCtaBanner: last 3 seconds)
  if (ev.outroEnabled) {
    const outroFrame = ev.outroStartFrame ?? ev.durationInFrames - 90;
    cues.push({ frame: Math.max(0, outroFrame), category: "ding", volume: 0.8 });
  }
  return cues;
};

const resolveCues = (cues: SfxCue[], minGapFrames: number, durationInFrames: number) => {
  const sorted = [...cues]
    .filter((c) => c.frame >= 0 && c.frame < durationInFrames && (library[c.category]?.length ?? 0) > 0)
    .sort((a, b) => a.frame - b.frame);
  const kept: SfxCue[] = [];
  for (const cue of sorted) {
    const prev = kept[kept.length - 1];
    if (prev && cue.frame - prev.frame < minGapFrames) continue;
    kept.push(cue);
  }
  // Rotate variants per category so repeated cues don't sound identical
  const used: Partial<Record<SfxCategory, number>> = {};
  return kept.map((cue) => {
    const files = library[cue.category]!;
    const n = used[cue.category] ?? 0;
    used[cue.category] = n + 1;
    const index = cue.variant ? (cue.variant - 1) % files.length : n % files.length;
    return { ...cue, src: files[index] };
  });
};

export const SfxLayer: React.FC<{
  config?: SfxConfig;
  events: TimelineEvents;
}> = ({ config, events }) => {
  const cfg = { ...defaultSfxConfig, ...config };
  const cues = React.useMemo(() => {
    if (!cfg.enabled) return [];
    const all = [...(cfg.auto ? buildAutoSfxCues(events) : []), ...(config?.cues ?? [])];
    return resolveCues(all, cfg.minGapFrames, events.durationInFrames);
  }, [cfg.enabled, cfg.auto, cfg.minGapFrames, config?.cues, events]);

  return (
    <>
      {cues.map((cue, i) => (
        <Audio
          key={`${cue.frame}-${cue.category}-${i}`}
          name={`sfx:${cue.category}`}
          src={staticFile(cue.src)}
          from={cue.frame}
          volume={Math.min(1, cfg.masterVolume * (cue.volume ?? 1))}
        />
      ))}
    </>
  );
};
