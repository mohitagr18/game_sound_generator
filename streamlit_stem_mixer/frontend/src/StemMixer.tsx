// StemMixer.tsx

import React, { useState } from "react";
import { Howl } from "howler";

// Accept props from Streamlit via argument!
const StemMixer = (props: any) => {
  const currentStems = props.args.current_stems
    ? JSON.parse(props.args.current_stems)
    : [];
  const nextStems = props.args.next_stems
    ? JSON.parse(props.args.next_stems)
    : [];

  const [howls, setHowls] = useState<{ [stem: string]: Howl }>({});
  const [playing, setPlaying] = useState(false);

  // Simple UI for demonstration
  return (
    <div>
      <h3>Stem Mixer UI</h3>
      <div>
        <strong>Current Stems</strong>
        <ul>
          {currentStems.map((stem, idx) => (
            <li key={`cur-${idx}`}>{stem.stem_name}</li>
          ))}
        </ul>
        <strong>Next Stems</strong>
        <ul>
          {nextStems.map((stem, idx) => (
            <li key={`next-${idx}`}>{stem.stem_name}</li>
          ))}
        </ul>
      </div>
      <button onClick={() => setPlaying(!playing)}>
        {playing ? "Pause" : "Play"}
      </button>
    </div>
  );
};

// Just export the "pure" component
export default StemMixer;