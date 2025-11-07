import React from "react";
import { Howl } from "howler";
import { withStreamlitConnection, StreamlitComponentBase, Streamlit } from "streamlit-component-lib";

// Define the type for a stem object
type Stem = {
  filename: string;
  targetgain: number;
  fadeduration: number;
};

class MyComponent extends StreamlitComponentBase {
  render = () => {
    // Parse stems from args (sent as JSON string)
    const stems: Stem[] = this.props.args.current_stems
      ? JSON.parse(this.props.args.current_stems)
      : [];

    return (
      <div>
        <h2>TEST STRING 123456</h2>
        <p>Args: {JSON.stringify(this.props.args)}</p>

        {stems.length === 0 && <div>No stems found.</div>}

        {stems.map((stem: Stem, idx: number) => (
          <button
            key={idx}
            onClick={() => {
              const sound = new Howl({ src: ["/" + stem.filename] });
              sound.play();
              console.log(
                "Play called for:",
                stem.filename,
                "gain:",
                stem.targetgain,
                "fade:",
                stem.fadeduration
              );
            }}
            style={{ display: "block", margin: "6px 0" }}
          >
            Play {stem.filename}
          </button>
        ))}
      </div>
    );
  };
}

export default withStreamlitConnection(MyComponent);
