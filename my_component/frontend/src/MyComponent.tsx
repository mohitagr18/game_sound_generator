// ---------------------------------------------------------------------------
// MyComponent.tsx (Streamlit Custom Component for Stem Mixing, Play, Fade)
// ---------------------------------------------------------------------------
// Step-by-step overview:
// 1. Imports React, Howler.js (audio playback), Streamlit Component connector.
// 2. Declares strong types for stems and internal state.
// 3. Main class: Handles play button logic, parses stems from props, triggers fade out/in
//    for current/next theme stems using Howler.js.
// 4. UI: Displays a "Play Mix" button with Streamlit-style looks,
//    and animated visual indicator ("Playing...") while active.
// ---------------------------------------------------------------------------

import React from "react";
import { Howl } from "howler";
import { withStreamlitConnection, StreamlitComponentBase, Streamlit } from "streamlit-component-lib";

// ---------------------------------------------------------------------------
// Stem type: Models a single track in the mix.
// ---------------------------------------------------------------------------
type Stem = {
  filename: string;
  targetgain: number;
  fadeduration: number;
};

// Internal UI state for play/fade indicator
type State = {
  isPlaying: boolean;
  playDuration: number; // ms
};

// ---------------------------------------------------------------------------
// Main Stem Mixer Component
// ---------------------------------------------------------------------------
class MyComponent extends StreamlitComponentBase<State> {
  constructor(props: any) {
    super(props);
    this.state = {
      isPlaying: false,
      playDuration: 3000, // fallback duration for UI indicator (in ms)
    };
  }

  /**
   * When Play Mix is clicked:
   *  - Fades out all current stems (theme 1)
   *  - Fades in all next stems (theme 2)
   *  - Keeps UI indicator active for max fade duration (shows animated soundwaves)
   */
  playMix = () => {
    // Parse stems from incoming props (as JSON string)
    const currentStems: Stem[] = this.props.args.current_stems
      ? JSON.parse(this.props.args.current_stems)
      : [];
    const nextStems: Stem[] = this.props.args.next_stems
      ? JSON.parse(this.props.args.next_stems)
      : [];
    // Calculate max fade duration (keep UI indicator visible accordingly)
    let maxFade = 0;
    [...currentStems, ...nextStems].forEach((stem: Stem) => {
      if (stem.fadeduration * 1000 > maxFade) maxFade = stem.fadeduration * 1000;
    });

    // Fade out current stems
    currentStems.forEach((stem: Stem, idx: number) => {
      const sound = new Howl({ src: ["/" + stem.filename] });
      sound.volume(stem.targetgain);
      sound.play();
      sound.fade(stem.targetgain, 0, stem.fadeduration * 1000);
      console.log("Fading out current stem:", stem.filename, "from gain", stem.targetgain, "in", stem.fadeduration, "sec");
    });

    // Fade in next stems
    nextStems.forEach((stem: Stem, idx: number) => {
      const sound = new Howl({ src: ["/" + stem.filename] });
      sound.volume(0);
      sound.play();
      sound.fade(0, stem.targetgain, stem.fadeduration * 1000);
      console.log("Fading in next stem:", stem.filename, "to gain", stem.targetgain, "in", stem.fadeduration, "sec");
    });

    // UI: Show "Playing..." for max fade duration, then revert
    this.setState({ isPlaying: true, playDuration: maxFade || 3000 });
    setTimeout(() => {
      this.setState({ isPlaying: false });
    }, maxFade || 3000);
  };

  // ---------------------------------------------------------------------------
  // Main Render: Shows the Play Mix button, and animates an indicator while active.
  // ---------------------------------------------------------------------------
  render = () => {
    // Parse stems for display (in case you want to render details)
    const stems: Stem[] = this.props.args.current_stems
      ? JSON.parse(this.props.args.current_stems)
      : [];

    // Streamlit-style button for visual consistency
    const streamlitButtonStyle: React.CSSProperties = {
      backgroundColor: "#F1F5FB",
      border: "1px solid #CCCCCC",
      color: "#262730",
      fontSize: "18px",
      padding: "0.5em 1.5em",
      borderRadius: "0.5em",
      cursor: this.state.isPlaying ? "not-allowed" : "pointer",
      fontWeight: 500,
      outline: "none",
      transition: "background 0.25s, box-shadow 0.25s",
      boxShadow: this.state.isPlaying ? "0 0 0 2px #AADFF8" : "none",
      position: "relative",
      marginTop: "10px",
      marginBottom: "10px"
    };

    // Animated soundwave bars ("playing" visual cue)
    const soundWaveAnim = (
      <div style={{
        display: "flex", alignItems: "center", gap: "0.5em",
        marginTop: "10px"
      }}>
        <span style={{fontWeight: 600}}>Playing…</span>
        <div style={{display: "inline-flex", gap: "2px"}}>
          {[1,2,3,4,5].map(i => (
            <div key={i} style={{
              width: "4px",
              height: `${8 + Math.abs((i * this.state.playDuration / 100) % 14)}px`,
              background: "#0984e3",
              borderRadius: "2px",
              animation: `waveAnim 0.9s infinite ease-in-out`,
              animationDelay: `${i*0.08}s`
            }} />
          ))}
        </div>
        <style>{`
          @keyframes waveAnim {
            0% { opacity: 0.7; height: 8px;}
            50% { opacity: 1; height: 18px;}
            100% { opacity: 0.7; height: 8px;}
          }
        `}</style>
      </div>
    );

    return (
      <div>
        {/* Show if no stems were found */}
        {stems.length === 0 && <div>No stems found.</div>}

        {/* Play Mix button, disables when playing is active */}
        <button
          style={streamlitButtonStyle}
          onClick={this.playMix}
          disabled={this.state.isPlaying}
          aria-busy={this.state.isPlaying}
          aria-live="polite"
        >
          {this.state.isPlaying ? "Playing…" : "Play Mix"}
        </button>

        {/* Show animated soundwave when "playing" */}
        {this.state.isPlaying && soundWaveAnim}
      </div>
    );
  };
}

// Export as a Streamlit-connected component
export default withStreamlitConnection(MyComponent);
