import React from "react";
import { AbsoluteFill } from "remotion";

/**
 * Universal Mobile Safe Zone Guide
 * Visualizes the safe area boundaries for 9:16 displays (iPhone 15 Pro Max, S24 Ultra)
 * and TikTok/Shorts UI overlays (Right buttons, Bottom captions, Top tabs).
 */
export const SafeZoneGuide: React.FC<{ enabled?: boolean }> = ({ enabled = false }) => {
  if (!enabled) return null;

  return (
    <AbsoluteFill
      style={{
        pointerEvents: "none",
        zIndex: 999,
      }}
    >
      {/* Universal Safe Zone Box: Width 860px (Margin Left/Right 110px), Y 285px to 1530px */}
      <div
        style={{
          position: "absolute",
          top: 285,
          left: 110,
          width: 860,
          height: 1245,
          border: "2px dashed #00F5D4",
          borderRadius: 20,
          boxShadow: "0 0 15px rgba(0, 245, 212, 0.4)",
        }}
      >
        <span
          style={{
            position: "absolute",
            top: 8,
            left: 12,
            backgroundColor: "rgba(0, 245, 212, 0.9)",
            color: "#000000",
            fontSize: 12,
            fontWeight: 800,
            padding: "2px 8px",
            borderRadius: 6,
          }}
        >
          UNIVERSAL SAFE ZONE (860px - ZERO UI CLASH)
        </span>
      </div>

      {/* Top Danger Zone (Dynamic Island, Camera notch, Tabs, TikTok Search Bar) */}
      <div
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          right: 0,
          height: 285,
          backgroundColor: "rgba(239, 68, 68, 0.15)",
          borderBottom: "1px solid rgba(239, 68, 68, 0.6)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "#EF4444",
          fontSize: 14,
          fontWeight: 700,
        }}
      >
        TOP DANGER ZONE (Notch / Dynamic Island / Search Bar Y=0-285)
      </div>

      {/* Right Danger Zone (TikTok / Shorts Action Column: Like, Comment, Share) */}
      <div
        style={{
          position: "absolute",
          top: 210,
          right: 0,
          width: 110,
          height: 1320,
          backgroundColor: "rgba(239, 68, 68, 0.15)",
          borderLeft: "1px solid rgba(239, 68, 68, 0.6)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "#EF4444",
          fontSize: 11,
          fontWeight: 700,
          writingMode: "vertical-rl",
        }}
      >
        RIGHT UI (Like / Comment / Share)
      </div>

      {/* Left Margin Indicator */}
      <div
        style={{
          position: "absolute",
          top: 210,
          left: 0,
          width: 110,
          height: 1320,
          backgroundColor: "rgba(239, 68, 68, 0.08)",
          borderRight: "1px solid rgba(239, 68, 68, 0.3)",
        }}
      />

      {/* Bottom Danger Zone (Username, Captions, Audio Title, Scrubber) */}
      <div
        style={{
          position: "absolute",
          bottom: 0,
          left: 0,
          right: 0,
          height: 390,
          backgroundColor: "rgba(239, 68, 68, 0.15)",
          borderTop: "1px solid rgba(239, 68, 68, 0.6)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "#EF4444",
          fontSize: 14,
          fontWeight: 700,
        }}
      >
        BOTTOM DANGER ZONE (Account / Multi-line Captions / Audio Bar)
      </div>
    </AbsoluteFill>
  );
};
