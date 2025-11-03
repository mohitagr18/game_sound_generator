// import React from "react";
// import ReactDOM from "react-dom";
// import StemMixer from "./StemMixer.tsx";

// ReactDOM.render(
//   <StemMixer />,
//   document.getElementById("root")
// );


// index.tsx

// import { withStreamlitConnection } from "streamlit-component-lib";
// import StemMixer from "./StemMixer.tsx"; // <-- The fix: Explicitly add .tsx

// // This is the correct Streamlit component entry point
// export default withStreamlitConnection(StemMixer);


// index.tsx

// import { withStreamlitConnection } from "streamlit-component-lib";
// import StemComponent from "./StemComponent"; // <-- UPDATED name

// // UPDATED export
// export default withStreamlitConnection(StemComponent);

// index.tsx

import { withStreamlitConnection } from "streamlit-component-lib";
import StemPlayer from "./StemPlayer"; // <-- UPDATED to new name

export default withStreamlitConnection(StemPlayer); // <-- UPDATED to new name