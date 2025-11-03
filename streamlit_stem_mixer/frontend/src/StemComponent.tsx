// StemComponent.tsx (or StemMixer.tsx)

import React, { useState } from "react";
import { Howl } from "howler";

// 1. DEFINE THE INTERFACE HERE
interface Stem {
  stem_name: string;
  // Add any other properties your stem object has
}

const StemComponent = (props: any) => { 
  // 2. USE THE INTERFACE to type your arrays
  const currentStems: Stem[] = props.args.current_stems
    ? JSON.parse(props.args.current_stems)
    : [];
  const nextStems: Stem[] = props.args.next_stems
    ? JSON.parse(props.args.next_stems)
    : [];

  const [howls, setHowls] = useState<{ [stem: string]: Howl }>({});
  const [playing, setPlaying] = useState(false);

  return (
    <div>
      <h3>Stem Mixer UI</h3>
      <div>
        <strong>Current Stems</strong>
        <ul>
          {/* 3. USE THE INTERFACE to type the 'stem' parameter */}
          {currentStems.map((stem: Stem, idx) => (
            <li key={`cur-${idx}`}>{stem.stem_name}</li>
          ))}
        </ul>
        <strong>Next Stems</strong>
        <ul>
          {/* Also add the type here for consistency */}
          {nextStems.map((stem: Stem, idx) => (
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

export default StemComponent;