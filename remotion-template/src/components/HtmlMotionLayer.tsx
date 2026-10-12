import React from "react";
import {
  Easing,
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

export type HtmlMotionItem = {
  type: "browser" | "tweet" | "search" | "notification";
  startFrame: number;
  endFrame: number;
  // Browser props
  url?: string;
  headline?: string;
  subheadline?: string;
  sourceName?: string;
  /** Real page capture from web_capture.py (public/ path, e.g. "screens/x.png"); replaces the fake article */
  screenshot?: string;
  /** Screenshot height / width, so the card can scroll through it */
  screenshotAspect?: number;
  // Tweet props
  authorName?: string;
  authorHandle?: string;
  tweetText?: string;
  likesCount?: string;
  retweetsCount?: string;
  // Search props
  searchQuery?: string;
  // Notification props
  appName?: string;
  notifTitle?: string;
  notifMessage?: string;
};

// Visible page area under the URL bar: keeps the card between the headline banner and the subtitles
const SCREENSHOT_VIEW_HEIGHT = 560;

export const HtmlMotionLayer: React.FC<{
  items?: HtmlMotionItem[];
}> = ({ items = [] }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const activeItem = items.find(
    (item) => frame >= item.startFrame && frame <= item.endFrame,
  );

  if (!activeItem) return null;

  const age = frame - activeItem.startFrame;
  const remaining = activeItem.endFrame - frame;

  // Spring entrance
  const popSpring = spring({
    frame: age,
    fps,
    config: { damping: 11, stiffness: 150, mass: 0.75 },
  });

  const scale = interpolate(popSpring, [0, 1], [0.8, 1]);
  const enterOpacity = interpolate(age, [0, 5], [0, 1], {
    extrapolateRight: "clamp",
  });
  const exitOpacity = interpolate(remaining, [0, 6], [0, 1], {
    extrapolateLeft: "clamp",
  });
  const opacity = Math.min(enterOpacity, exitOpacity);

  // 1. BROWSER MOCKUP (Safari / Chrome News Headline)
  if (activeItem.type === "browser") {
    const url =
      activeItem.url || "https://reuters.com/investigates/clancy-trial";
    const typedChars = Math.min(url.length, Math.floor(age * 1.5));
    const currentUrl = url.slice(0, typedChars);

    // Screenshot scroll: hold the top of the page (title) for the first 40% so it can be read,
    // then glide down at most ~6px per frame so short placements don't whip past the content
    const itemDuration = activeItem.endFrame - activeItem.startFrame;
    const scrollStart = Math.max(18, Math.round(itemDuration * 0.4));
    const scrollEnd = Math.max(scrollStart + 1, itemDuration - 8);
    const screenshotScroll = interpolate(
      age,
      [scrollStart, scrollEnd],
      [
        0,
        Math.min(
          Math.max(
            0,
            840 * (activeItem.screenshotAspect ?? 0) - SCREENSHOT_VIEW_HEIGHT,
          ),
          SCREENSHOT_VIEW_HEIGHT * 0.9,
          (scrollEnd - scrollStart) * 6,
        ),
      ],
      {
        extrapolateLeft: "clamp",
        extrapolateRight: "clamp",
        easing: Easing.inOut(Easing.cubic),
      },
    );

    return (
      <div
        style={{
          position: "absolute",
          top: "46%",
          left: "50%",
          transform: `translate(-50%, -50%) scale(${scale})`,
          width: 840,
          zIndex: 43,
          opacity,
          backgroundColor: "#18181B",
          borderRadius: 22,
          border: "2px solid rgba(255, 255, 255, 0.15)",
          boxShadow: "0 30px 75px rgba(0,0,0,0.9), 0 0 35px rgba(0,0,0,0.5)",
          overflow: "hidden",
        }}
      >
        {/* Browser Top Bar */}
        <div
          style={{
            height: 48,
            backgroundColor: "#27272A",
            display: "flex",
            alignItems: "center",
            padding: "0 18px",
            gap: 12,
            borderBottom: "1px solid rgba(255,255,255,0.08)",
          }}
        >
          {/* Window control dots */}
          <div style={{ display: "flex", gap: 8 }}>
            <div
              style={{
                width: 14,
                height: 14,
                borderRadius: "50%",
                backgroundColor: "#EF4444",
              }}
            />
            <div
              style={{
                width: 14,
                height: 14,
                borderRadius: "50%",
                backgroundColor: "#F59E0B",
              }}
            />
            <div
              style={{
                width: 14,
                height: 14,
                borderRadius: "50%",
                backgroundColor: "#10B981",
              }}
            />
          </div>

          {/* URL Pill Bar */}
          <div
            style={{
              flex: 1,
              backgroundColor: "#18181B",
              borderRadius: 10,
              height: 32,
              display: "flex",
              alignItems: "center",
              padding: "0 14px",
              gap: 8,
              fontSize: 14,
              color: "#A1A1AA",
              fontFamily: "monospace",
            }}
          >
            <span>🔒</span>
            <span style={{ color: "#E4E4E7" }}>{currentUrl}</span>
            {age % 15 < 8 && <span style={{ color: "#3B82F6" }}>|</span>}
          </div>
        </div>

        {/* Real page screenshot: slow scroll through the capture after a short read pause */}
        {activeItem.screenshot ? (
          <div
            style={{
              height: SCREENSHOT_VIEW_HEIGHT,
              overflow: "hidden",
              backgroundColor: "#09090B",
            }}
          >
            <Img
              src={staticFile(
                activeItem.screenshot
                  .replace(/\\/g, "/")
                  .replace(/^.*public\//, ""),
              )}
              style={{
                width: "100%",
                display: "block",
                transform: `translateY(${-screenshotScroll}px)`,
              }}
            />
          </div>
        ) : (
          <div style={{ padding: "32px 36px", backgroundColor: "#09090B" }}>
            {activeItem.sourceName && (
              <div
                style={{
                  color: "#3B82F6",
                  fontSize: 15,
                  fontWeight: 900,
                  letterSpacing: "1.5px",
                  textTransform: "uppercase",
                  marginBottom: 10,
                }}
              >
                📰 {activeItem.sourceName}
              </div>
            )}
            <h2
              style={{
                color: "#FFFFFF",
                fontSize: 34,
                fontWeight: 900,
                lineHeight: 1.25,
                margin: 0,
                marginBottom: 14,
              }}
            >
              {activeItem.headline ||
                "Breaking: Shocking Public Debate Surrounding Viral Trial"}
            </h2>
            {activeItem.subheadline && (
              <p
                style={{
                  color: "#D4D4D8",
                  fontSize: 20,
                  lineHeight: 1.45,
                  margin: 0,
                  fontWeight: 500,
                }}
              >
                {activeItem.subheadline}
              </p>
            )}
          </div>
        )}
      </div>
    );
  }

  // 2. TWEET / X POST MOCKUP
  if (activeItem.type === "tweet") {
    return (
      <div
        style={{
          position: "absolute",
          top: "46%",
          left: "50%",
          transform: `translate(-50%, -50%) scale(${scale})`,
          width: 840,
          zIndex: 43,
          opacity,
          backgroundColor: "#000000",
          borderRadius: 24,
          border: "2px solid #2F3336",
          boxShadow:
            "0 25px 65px rgba(0,0,0,0.9), 0 0 30px rgba(29, 155, 240, 0.2)",
          padding: "28px 32px",
        }}
      >
        {/* Tweet Header */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 14,
            marginBottom: 18,
          }}
        >
          <div
            style={{
              width: 54,
              height: 54,
              borderRadius: "50%",
              backgroundColor: "#1D9BF0",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 24,
              fontWeight: 900,
              color: "#FFFFFF",
            }}
          >
            {(activeItem.authorName || "X")[0]}
          </div>
          <div style={{ display: "flex", flexDirection: "column" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <span style={{ color: "#FFFFFF", fontSize: 22, fontWeight: 800 }}>
                {activeItem.authorName || "Viral Insights"}
              </span>
              <span style={{ color: "#1D9BF0", fontSize: 18 }}>✓</span>
            </div>
            <span style={{ color: "#71767B", fontSize: 16 }}>
              {activeItem.authorHandle || "@viralinsights"}
            </span>
          </div>
        </div>

        {/* Tweet Body */}
        <div
          style={{
            color: "#E7E9EA",
            fontSize: 28,
            fontWeight: 600,
            lineHeight: 1.35,
            marginBottom: 20,
          }}
        >
          {activeItem.tweetText ||
            "I can't believe what is trending on my timeline right now."}
        </div>

        {/* Tweet Footer Stats */}
        <div
          style={{
            display: "flex",
            gap: 36,
            paddingTop: 16,
            borderTop: "1px solid #2F3336",
            color: "#71767B",
            fontSize: 18,
            fontWeight: 700,
          }}
        >
          <span>🔁 {activeItem.retweetsCount || "14.2K"} Retweets</span>
          <span>❤️ {activeItem.likesCount || "89.5K"} Likes</span>
        </div>
      </div>
    );
  }

  // 3. SEARCH ENGINE MOCKUP (Google / Safari Search Bar)
  if (activeItem.type === "search") {
    const query = activeItem.searchQuery || "who has hurt women more";
    const typedChars = Math.min(query.length, Math.floor(age * 1.6));
    const currentQuery = query.slice(0, typedChars);

    return (
      <div
        style={{
          position: "absolute",
          top: "46%",
          left: "50%",
          transform: `translate(-50%, -50%) scale(${scale})`,
          width: 840,
          zIndex: 43,
          opacity,
          backgroundColor: "#202124",
          borderRadius: 32,
          border: "2px solid rgba(255, 255, 255, 0.2)",
          boxShadow:
            "0 25px 60px rgba(0,0,0,0.9), 0 0 40px rgba(66, 133, 244, 0.25)",
          padding: "20px 32px",
          display: "flex",
          alignItems: "center",
          gap: 16,
        }}
      >
        <span style={{ fontSize: 28 }}>🔍</span>
        <span
          style={{
            color: "#FFFFFF",
            fontSize: 28,
            fontWeight: 700,
            flex: 1,
            letterSpacing: "-0.2px",
          }}
        >
          {currentQuery}
          {age % 14 < 7 && <span style={{ color: "#4285F4" }}>|</span>}
        </span>
        <span style={{ fontSize: 24, opacity: 0.8 }}>🎙️</span>
      </div>
    );
  }

  // 4. NOTIFICATION POPUP (iOS Style)
  return (
    <div
      style={{
        position: "absolute",
        top: 260,
        left: "50%",
        transform: `translateX(-50%) scale(${scale})`,
        width: 840,
        zIndex: 44,
        opacity,
        backgroundColor: "rgba(30, 41, 59, 0.95)",
        backdropFilter: "blur(20px)",
        borderRadius: 24,
        border: "1px solid rgba(255, 255, 255, 0.2)",
        boxShadow: "0 20px 50px rgba(0,0,0,0.8)",
        padding: "18px 24px",
        display: "flex",
        alignItems: "center",
        gap: 18,
      }}
    >
      <div
        style={{
          width: 48,
          height: 48,
          borderRadius: 12,
          backgroundColor: "#3B82F6",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 24,
        }}
      >
        💬
      </div>
      <div
        style={{ flex: 1, display: "flex", flexDirection: "column", gap: 3 }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <span
            style={{
              color: "#94A3B8",
              fontSize: 14,
              fontWeight: 700,
              textTransform: "uppercase",
            }}
          >
            {activeItem.appName || "NEWS ALERT"}
          </span>
          <span style={{ color: "#64748B", fontSize: 13 }}>now</span>
        </div>
        <span style={{ color: "#FFFFFF", fontSize: 19, fontWeight: 800 }}>
          {activeItem.notifTitle || "Trending Topic Update"}
        </span>
        <span style={{ color: "#CBD5E1", fontSize: 16, fontWeight: 500 }}>
          {activeItem.notifMessage ||
            "Online discussion reaches 2.4 million impressions."}
        </span>
      </div>
    </div>
  );
};
