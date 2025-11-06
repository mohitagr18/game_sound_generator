import React, { useRef } from "react";
import { Howl } from "howler";
import { withStreamlitConnection, StreamlitComponentBase, Streamlit } from "streamlit-component-lib";

class MyComponent extends StreamlitComponentBase {
  sound: Howl | null = null;

  handlePlay = () => {
  const filename = this.props.args.name;
  this.sound = new Howl({
    src: [filename]
  });
  console.log("Play called for:", filename);
  this.sound.play();
};




  render = () => {
    return (
      <div>
        <h2>TEST STRING 123456</h2>
        <p>Args: {JSON.stringify(this.props.args)}</p>
        <button onClick={this.handlePlay}>Play sound.mp3</button>
      </div>
    );
  };
}

export default withStreamlitConnection(MyComponent);




// import React, { useRef } from "react";
// import { Howl } from "howler";

// interface Props {
//   args?: unknown;
// }

// const MyComponent: React.FC<Props> = (props) => {
//   const soundRef = useRef<Howl | null>(null);

//   const handlePlay = () => {
//     if (!soundRef.current) {
//       soundRef.current = new Howl({
//         src: ["/sound.mp3"] // Path is relative to your public/build directory
//       });
//     }
//     soundRef.current.play();
//   };

//   return (
//     <div>
//       <h2>TEST STRING 123456</h2>
//       <p>Args: {JSON.stringify(props.args)}</p>
//       <button onClick={handlePlay}>Play sound.mp3</button>
//     </div>
//   );
// };

// export default MyComponent;
