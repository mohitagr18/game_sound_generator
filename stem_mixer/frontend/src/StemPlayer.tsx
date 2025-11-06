import React, { useState } from "react";
import { Howl } from "howler";

// Explicitly define the interface for your stems
interface Stem {
  stem_name: string;
  // Add other fields if needed
}

interface StemPlayerProps {
  args: {
    current_stems?: string;
    next_stems?: string;
  };
}

const StemPlayer = (props: StemPlayerProps) => {
  // Parse and type your stems
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
      <h3>Stem Player UI</h3>
      <div>
        <strong>Current Stems</strong>
        <ul>
          {currentStems.map((stem: Stem, idx: number) => (
            <li key={`cur-${idx}`}>{stem.stem_name}</li>
          ))}
        </ul>
        <strong>Next Stems</strong>
        <ul>
          {nextStems.map((stem: Stem, idx: number) => (
            <li key={`next-${idx}`}>{stem.stem_name}</li>
          ))}
        </ul>
      </div>
      <div>
        <button onClick={() => setPlaying(!playing)}>
          {playing ? "Pause" : "Play"}
        </button>
      </div>
    </div>
  );
};

export default StemPlayer;
