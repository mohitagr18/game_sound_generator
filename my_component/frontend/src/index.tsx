import React from "react";
import { createRoot } from "react-dom/client";
import MyComponent from "./MyComponent";
import { Streamlit } from "streamlit-component-lib";

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Root element not found");
}

const root = createRoot(rootElement);

root.render(
  <React.StrictMode>
    <MyComponent />
  </React.StrictMode>
);

// Notify Streamlit that the component finished rendering
Streamlit.setComponentReady();

// (Optional but recommended for automatic sizing)
Streamlit.setFrameHeight();
