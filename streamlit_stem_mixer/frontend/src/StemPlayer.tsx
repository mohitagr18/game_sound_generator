// StemPlayer.tsx
import { useState } from "react";
import { Howl } from "howler";

// Explicitly define the interface for your stems
interface Stem {
  stem_name: string;
}

interface StemPlayerProps {
  args: {
    current_stems?: string;
    next_stems?: string;
  };
}

const StemPlayer = (props: StemPlayerProps) => {
  // Parse and type your stems
  const currentStems: Array<Stem> = props.args.current_stems 
    ? JSON.parse(props.args.current_stems) 
    : [];
  const nextStems: Array<Stem> = props.args.next_stems 
    ? JSON.parse(props.args.next_stems) 
    : [];

  const [howls, setHowls] = useState<Record<string, Howl>>({});
  const [playing, setPlaying] = useState<boolean>(false);

  return (
    <div>
      <h3>Stem Player UI</h3>
      <div>
        <strong>Current Stems</strong>
        <ul>
          {currentStems.map(function(stem: Stem, idx: number) {
            return <li key={`cur-${idx}`}>{stem.stem_name}</li>;
          })}
        </ul>
        <strong>Next Stems</strong>
        <ul>
          {nextStems.map(function(stem: Stem, idx: number) {
            return <li key={`next-${idx}`}>{stem.stem_name}</li>;
          })}
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