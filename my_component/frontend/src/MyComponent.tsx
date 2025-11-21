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



// import React from "react";
// import { Howl } from "howler";
// import { withStreamlitConnection, StreamlitComponentBase, Streamlit } from "streamlit-component-lib";

// // ---------------------------------------------------------------------------
// // Stem type: Models a single track in the mix.
// // ---------------------------------------------------------------------------
// type Stem = {
//   filename: string;
//   targetgain: number;
//   fadeduration: number;
// };

// // Internal UI state for play/fade indicator
// type State = {
//   isPlaying: boolean;
//   playDuration: number; // ms
// };

// // ---------------------------------------------------------------------------
// // Main Stem Mixer Component
// // ---------------------------------------------------------------------------
// class MyComponent extends StreamlitComponentBase<State> {
//   constructor(props: any) {
//     super(props);
//     this.state = {
//       isPlaying: false,
//       playDuration: 3000, // fallback duration for UI indicator (in ms)
//     };
//   }

//   /**
//    * When Play Mix is clicked:
//    *  - Fades out all current stems (theme 1)
//    *  - Fades in all next stems (theme 2)
//    *  - Keeps UI indicator active for max fade duration (shows animated soundwaves)
//    */
//   playMix = () => {
//     // Parse stems from incoming props (as JSON string)
//     const currentStems: Stem[] = this.props.args.current_stems
//       ? JSON.parse(this.props.args.current_stems)
//       : [];
//     const nextStems: Stem[] = this.props.args.next_stems
//       ? JSON.parse(this.props.args.next_stems)
//       : [];
//     // Calculate max fade duration (keep UI indicator visible accordingly)
//     let maxFade = 0;
//     [...currentStems, ...nextStems].forEach((stem: Stem) => {
//       if (stem.fadeduration * 1000 > maxFade) maxFade = stem.fadeduration * 1000;
//     });

//     // Fade out current stems
//     currentStems.forEach((stem: Stem, idx: number) => {
//       // const sound = new Howl({ src: ["http://localhost:8501/audio_clips/" + stem.filename] });
//       const url = "http://localhost:9000/audio_clips/" + stem.filename;
//       console.log("Requesting audio URL (current):", url);
//       const sound = new Howl({ src: [url] });
//       sound.volume(stem.targetgain);
//       sound.play();
//       sound.fade(stem.targetgain, 0, stem.fadeduration * 1000);
//       console.log("Fading out current stem:", stem.filename, "from gain", stem.targetgain, "in", stem.fadeduration, "sec");
//     });

//     // Fade in next stems
//     nextStems.forEach((stem: Stem, idx: number) => {
//       // const sound = new Howl({ src: ["http://localhost:8501/audio_clips/" + stem.filename] });
//       const url = "http://localhost:9000/audio_clips/" + stem.filename;
//       console.log("Requesting audio URL (current):", url);
//       const sound = new Howl({ src: [url] });
//       sound.volume(0);
//       sound.play();
//       sound.fade(0, stem.targetgain, stem.fadeduration * 1000);
//       console.log("Fading in next stem:", stem.filename, "to gain", stem.targetgain, "in", stem.fadeduration, "sec");
//     });

//     // UI: Show "Playing..." for max fade duration, then revert
//     this.setState({ isPlaying: true, playDuration: maxFade || 3000 });
//     setTimeout(() => {
//       this.setState({ isPlaying: false });
//     }, maxFade || 3000);
//   };

//   // ---------------------------------------------------------------------------
//   // Main Render: Shows the Play Mix button, and animates an indicator while active.
//   // ---------------------------------------------------------------------------
//   render = () => {
//     // Parse stems for display (in case you want to render details)
//     const stems: Stem[] = this.props.args.current_stems
//       ? JSON.parse(this.props.args.current_stems)
//       : [];

//     // Streamlit-style button for visual consistency
//     const streamlitButtonStyle: React.CSSProperties = {
//       backgroundColor: "#F1F5FB",
//       border: "1px solid #CCCCCC",
//       color: "#262730",
//       fontSize: "18px",
//       padding: "0.5em 1.5em",
//       borderRadius: "0.5em",
//       cursor: this.state.isPlaying ? "not-allowed" : "pointer",
//       fontWeight: 500,
//       outline: "none",
//       transition: "background 0.25s, box-shadow 0.25s",
//       boxShadow: this.state.isPlaying ? "0 0 0 2px #AADFF8" : "none",
//       position: "relative",
//       marginTop: "10px",
//       marginBottom: "10px"
//     };

//     // Animated soundwave bars ("playing" visual cue)
//     const soundWaveAnim = (
//       <div style={{
//         display: "flex", alignItems: "center", gap: "0.5em",
//         marginTop: "10px"
//       }}>
//         <span style={{fontWeight: 600}}>Playing…</span>
//         <div style={{display: "inline-flex", gap: "2px"}}>
//           {[1,2,3,4,5].map(i => (
//             <div key={i} style={{
//               width: "4px",
//               height: `${8 + Math.abs((i * this.state.playDuration / 100) % 14)}px`,
//               background: "#0984e3",
//               borderRadius: "2px",
//               animation: `waveAnim 0.9s infinite ease-in-out`,
//               animationDelay: `${i*0.08}s`
//             }} />
//           ))}
//         </div>
//         <style>{`
//           @keyframes waveAnim {
//             0% { opacity: 0.7; height: 8px;}
//             50% { opacity: 1; height: 18px;}
//             100% { opacity: 0.7; height: 8px;}
//           }
//         `}</style>
//       </div>
//     );

//     return (
//       <div>
//         {/* Show if no stems were found */}
//         {stems.length === 0 && <div>No stems found.</div>}

//         {/* Play Mix button, disables when playing is active */}
//         <button
//           style={streamlitButtonStyle}
//           onClick={this.playMix}
//           disabled={this.state.isPlaying}
//           aria-busy={this.state.isPlaying}
//           aria-live="polite"
//         >
//           {this.state.isPlaying ? "Playing…" : "Play Mix"}
//         </button>

//         {/* Show animated soundwave when "playing" */}
//         {this.state.isPlaying && soundWaveAnim}
//       </div>
//     );
//   };
// }

// // Export as a Streamlit-connected component
// export default withStreamlitConnection(MyComponent);
