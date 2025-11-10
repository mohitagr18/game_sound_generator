// ---------------------------------------------------------------------------
// index.tsx / index.js
//
// Step-by-step overview:
// 1. Import React, ReactDOM, and the custom Streamlit component.
// 2. Get the main root element from the HTML (for attach point).
// 3. Create a root for React rendering (React 18+ API).
// 4. Render the MyComponent component inside React.StrictMode for better dev checks.
// 5. Notify Streamlit that the component is ready.
// 6. Optionally auto-resize the frame to fit content.
// ---------------------------------------------------------------------------

import React from "react";
import { createRoot } from "react-dom/client";
import MyComponent from "./MyComponent";
import { Streamlit } from "streamlit-component-lib";

// Get the root DOM element (#root should always exist in Streamlit components)
const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Root element not found");
}

// Create React root (new API, React 18+)
const root = createRoot(rootElement);

// Render the main custom component ("MyComponent") as a Streamlit child.
root.render(
  <React.StrictMode>
    <MyComponent />
  </React.StrictMode>
);

// Notify Streamlit that the component has finished initial render (required)
Streamlit.setComponentReady();

// (Optional but recommended for auto height fit)
Streamlit.setFrameHeight();
