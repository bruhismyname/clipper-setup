import React from "react";
import { interpolate, useCurrentFrame } from "remotion";
import { loadFont } from "@remotion/google-fonts/Montserrat";

/* -------------------------------------------------------------
 * ONE-WORD CAPTION (Style B "Fullbleed Speaker")
 * One spoken token at a time, plain white with a thin outline, sitting at
 * chest height (~46% of the canvas) just above the keyword overlay zone.
 * Numbers stay glued to their unit ("$1 billion", "10 years").
 * ------------------------------------------------------------- */

const { fontFamily } = loadFont("normal", { weights: ["700", "800"], subsets: ["latin"] });

export type CaptionWordInput = {
  text: string;
  startFrame: number;
  endFrame: number;
};

export type CaptionToken = { text: string; startFrame: number; endFrame: number };

export type OneWordCaptionConfig = {
  enabled?: boolean;
  centerY?: number;
  fontSize?: number;
  /** Hide the caption when nothing is said for longer than this */
  maxHoldFrames?: number;
};

const NUMBERISH = /^[$€£]?\d[\d.,]*[%kKmM]?$/;
const UNIT = /^(dollars?|bucks|million|billion|thousand|hundred|years?|months?|weeks?|days?|hours?|minutes?|seconds?|percent|times|k|grand|pounds?|feet|miles?)$/i;
const KEEP_CAPS = /^(I|I'm|I'll|I've|I'd|OK)$/;

const cleanWord = (w: string) => w.replace(/^[^\w$€£']+|[^\w%']+$/g, "");

export const buildCaptionTokens = (words: CaptionWordInput[], minFrames = 3): CaptionToken[] => {
  const tokens: CaptionToken[] = [];
  let sentenceStart = true;
  for (let i = 0; i < words.length; i++) {
    const raw = words[i].text.trim();
    let text = cleanWord(raw);
    const endsSentence = /[.?!]["')\]]*$/.test(raw);
    if (!text) {
      sentenceStart = sentenceStart || endsSentence;
      continue;
    }
    // Sentence-initial capitals read as shouting in one-word captions; keep "I" and acronyms
    if (sentenceStart && !KEEP_CAPS.test(text) && text.slice(1) === text.slice(1).toLowerCase()) {
      text = text.charAt(0).toLowerCase() + text.slice(1);
    }
    sentenceStart = endsSentence;

    const prev = tokens[tokens.length - 1];
    const prevIsNumber = prev && NUMBERISH.test(prev.text.split(" ").pop() ?? "");
    const tooShort = prev && prev.endFrame - prev.startFrame < minFrames && words[i].startFrame - prev.endFrame < 3;
    if (prev && ((prevIsNumber && UNIT.test(text)) || tooShort)) {
      prev.text = `${prev.text} ${text}`;
      prev.endFrame = words[i].endFrame;
      continue;
    }
    tokens.push({ text, startFrame: words[i].startFrame, endFrame: words[i].endFrame });
  }
  return tokens;
};

export const OneWordCaption: React.FC<{
  tokens: CaptionToken[];
  config?: OneWordCaptionConfig;
}> = ({ tokens, config }) => {
  const frame = useCurrentFrame();
  const { enabled = true, centerY = 880, fontSize = 78, maxHoldFrames = 12 } = config ?? {};
  if (!enabled || tokens.length === 0) return null;

  // Active token: the latest one that started; it holds until the next token or a long pause
  let idx = -1;
  for (let i = 0; i < tokens.length; i++) {
    if (tokens[i].startFrame <= frame) idx = i;
    else break;
  }
  if (idx === -1) return null;
  const tok = tokens[idx];
  const next = tokens[idx + 1];
  const holdUntil = Math.min(next ? next.startFrame : Infinity, tok.endFrame + maxHoldFrames);
  if (frame >= holdUntil) return null;

  const age = frame - tok.startFrame;
  return (
    <div
      style={{
        position: "absolute",
        left: 110,
        right: 110,
        top: centerY,
        translate: "0 -50%",
        display: "flex",
        justifyContent: "center",
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          fontFamily,
          fontWeight: 800,
          fontSize,
          lineHeight: 1.05,
          color: "#FFFFFF",
          textAlign: "center",
          letterSpacing: -0.5,
          WebkitTextStroke: "5px #000000",
          paintOrder: "stroke fill",
          textShadow: "0 4px 12px rgba(0,0,0,0.45)",
          scale: interpolate(age, [0, 3], [0.92, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
          opacity: interpolate(age, [0, 2], [0.6, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
        }}
      >
        {tok.text}
      </div>
    </div>
  );
};
