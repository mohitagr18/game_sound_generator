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

// ---------------------------------------------------------------------------
// MyComponent.tsx (Updated: With Stop Button & Persistent State)
// ---------------------------------------------------------------------------

import React from "react";
import { Howl } from "howler";
import { withStreamlitConnection, StreamlitComponentBase } from "streamlit-component-lib";

// ---------------------------------------------------------------------------
// Stem type
// ---------------------------------------------------------------------------
type Stem = {
  filename: string;
  targetgain: number;
  fadeduration: number;
};

// Internal UI state
type State = {
  isPlaying: boolean;
};

// ---------------------------------------------------------------------------
// Main Stem Mixer Component
// ---------------------------------------------------------------------------
class MyComponent extends StreamlitComponentBase<State> {
  // specific class property to track active audio instances
  private activeHowls: Howl[] = [];

  constructor(props: any) {
    super(props);
    this.state = {
      isPlaying: false,
    };
  }

  /**
   * Stops all currently playing sounds and resets state.
   */
  stopMix = () => {
    this.activeHowls.forEach(h => h.stop());
    this.activeHowls = []; // clear the list
    this.setState({ isPlaying: false });
  };

  /**
   * Plays the transition:
   * - Stops any previous mix first.
   * - Fades out current stems.
   * - Fades in next stems.
   * - Sets state to Playing (indefinitely, until user clicks Stop).
   */
  playMix = () => {
    // 1. Stop anything currently running to prevent chaotic layering
    this.stopMix();

    const currentStems: Stem[] = this.props.args.current_stems
      ? JSON.parse(this.props.args.current_stems)
      : [];
    const nextStems: Stem[] = this.props.args.next_stems
      ? JSON.parse(this.props.args.next_stems)
      : [];

    // 2. Fade out current stems
    currentStems.forEach((stem: Stem) => {
      const url = "http://localhost:9000/audio_clips/" + stem.filename;
      const sound = new Howl({ src: [url], loop: true }); // Assuming loop for game audio
      
      // Initialize at target volume, then fade to 0
      sound.volume(stem.targetgain);
      sound.play();
      sound.fade(stem.targetgain, 0, stem.fadeduration * 1000);
      
      // We generally don't track outgoing stems in 'activeHowls' because they die out quickly.
      // However, if we want the Stop button to kill them mid-fade, we should add them:
      this.activeHowls.push(sound);
      
      // Optional: Unload them after fade to save memory
      setTimeout(() => {
        sound.unload();
      }, (stem.fadeduration * 1000) + 1000);
    });

    // 3. Fade in next stems
    nextStems.forEach((stem: Stem) => {
      const url = "http://localhost:9000/audio_clips/" + stem.filename;
      const sound = new Howl({ src: [url], loop: true }); // Assuming loop for game audio
      
      // Initialize at 0, fade to target
      sound.volume(0);
      sound.play();
      sound.fade(0, stem.targetgain, stem.fadeduration * 1000);
      
      this.activeHowls.push(sound);
    });

    // 4. Update UI State
    this.setState({ isPlaying: true });
  };

  render = () => {
    const stems: Stem[] = this.props.args.current_stems
      ? JSON.parse(this.props.args.current_stems)
      : [];

    // Base Button Style
    const baseBtnStyle: React.CSSProperties = {
      border: "1px solid #CCCCCC",
      fontSize: "18px",
      padding: "0.5em 1.5em",
      borderRadius: "0.5em",
      cursor: "pointer",
      fontWeight: 500,
      outline: "none",
      transition: "all 0.2s",
      marginTop: "10px",
      marginBottom: "10px",
      width: "100%" 
    };

    // Conditional Styles for Play vs Stop
    const playStyle = {
      ...baseBtnStyle,
      backgroundColor: "#F1F5FB",
      color: "#262730",
    };

    const stopStyle = {
      ...baseBtnStyle,
      backgroundColor: "#ff4b4b", // Streamlit red
      color: "white",
      border: "1px solid #ff4b4b",
    };

    // Animated soundwave bars
    const soundWaveAnim = (
      <div style={{
        display: "flex", alignItems: "center", gap: "0.5em",
        marginTop: "10px", justifyContent: "center"
      }}>
        <span style={{fontWeight: 600, color: "#262730"}}>Now Playing…</span>
        <div style={{display: "inline-flex", gap: "3px", height: "20px", alignItems: "center"}}>
          {[1,2,3,4,5].map(i => (
            <div key={i} style={{
              width: "4px",
              height: "10px",
              background: "#0984e3",
              borderRadius: "2px",
              animation: `waveAnim 0.9s infinite ease-in-out`,
              animationDelay: `${i*0.1}s`
            }} />
          ))}
        </div>
        <style>{`
          @keyframes waveAnim {
            0% { opacity: 0.7; height: 8px;}
            50% { opacity: 1; height: 20px;}
            100% { opacity: 0.7; height: 8px;}
          }
        `}</style>
      </div>
    );

    return (
      <div>
        {stems.length === 0 && <div style={{marginBottom:10}}>Ready to mix.</div>}

        {/* Toggle Button: Shows STOP if playing, PLAY MIX if stopped */}
        {!this.state.isPlaying ? (
            <button style={playStyle} onClick={this.playMix}>
              ▶ Play Mix
            </button>
        ) : (
            <button style={stopStyle} onClick={this.stopMix}>
              ⏹ Stop Audio
            </button>
        )}

        {/* Show visual indicator only when playing */}
        {this.state.isPlaying && soundWaveAnim}
      </div>
    );
  };
}

export default withStreamlitConnection(MyComponent);
