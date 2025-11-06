import React from "react";
import ReactDOM from "react-dom";
import { withStreamlitConnection } from "streamlit-component-lib";
import StemPlayer from "./StemPlayer";

const ConnectedComponent = withStreamlitConnection(StemPlayer);

ReactDOM.render(
  <React.StrictMode>
    <ConnectedComponent />
  </React.StrictMode>,
  document.getElementById("root")
);
