# 🚀🎶 Game Sound Generator: Live Theme StemMix Demo

**AI-powered, cross-platform game audio mixing—mix themes, fade stems, and explore transitions in REAL time\!**

-----

## 🌟 Features

  - **Live Audio Stem Crossfade:** Instantly transition and blend music themes using multi-stem mixing with smooth gain and fade control.
  - **Smart AI Transitions:** Musical intent—stems, gains, fades—is generated on the fly by **Gemini LLM (Google AI)**.
  - **Cloud-Native Audio:** Audio stems are streamed directly from **Google Cloud Storage (GCS)** for low-latency, cross-platform playback.
  - **Interactive Dashboard:** Streamlit UI for selecting themes, exploring mixes, and tracking history.
  - **React + Howler.js Frontend:** Native, multi-track audio mixing with a persistent "Playing/Stop" control and animated soundwave indicator.
  - **Strict Hallucination Control:** The AI is grounded with real-time file inventory checks, ensuring it never recommends missing audio files.

-----

## 🧠✨ Gemini LLM Powers Musical Intelligence

**Gemini LLM isn’t just a backend—it’s the music director\!**

  - Given your themes, history, and session state, Gemini outputs a full musical “intent”:
      - Which stems to use (e.g., *drums, synth, pads*)
      - Gain and fade levels (e.g., *Fade drums in over 2.0s at 80% volume*)
      - Explanation/reasoning
  - This intent is fed directly to **Howler.js**—so *every mix you hear is AI-designed and explained\!*

-----

## 🏗️ Architecture: AI → Python → Cloud → Browser

This project uses a hybrid architecture where **Python** handles logic/AI, but the **Browser** streams heavy audio directly from the **Cloud**.

```mermaid
graph TD
    User[User] -->|Selects Theme| UI[Streamlit UI (Python)]
    UI -->|Context + File List| AI[Gemini LLM]
    AI -->|JSON Mix Intent| UI
    UI -->|Props: {files, gain, fade}| Frontend[React Component]
    Frontend -->|Fetch Audio| GCS[Google Cloud Storage]
    GCS -->|Stream .wav| Frontend
    Frontend -->|Mix & Play| User
```

| Layer       | Technology    | Role                                                      |
|-------------|--------------|-----------------------------------------------------------|
| **Control** | Streamlit    | 🖼️ User interface, theme logic, LLM request/response      |
| **Intelligence**| Gemini LLM | 🧠 Generates JSON intent: selects stems, gain, fade durations|
| **Assets** | Google Cloud Storage | ☁️ Hosts raw `.wav` stems (public bucket + CORS enabled) |
| **Playback**| React + Howler.js | 🎶 Browser-based mixing engine (receives JSON, streams from GCS)|

**How the Data Flows:**

1.  **Inventory Check:** Python scans the local directory to validate which stems exist (preventing AI hallucinations).
2.  **AI Request:** The app sends the valid file list + current theme to Gemini LLM (`llm_advisor.py`).
3.  **Intent Generation:** Gemini replies with a JSON plan (e.g., "Fade in `combat/drums.wav`").
4.  **Handoff:** Python passes this plan to the React frontend via the `stem_mixer.py` bridge.
5.  **Streaming:** The React component constructs the URL (`https://storage.googleapis.com/...`) and streams the audio using Howler.js.

-----

## 📁 Project Structure

```plaintext
game_sound_generator/
├── demo2_st.py             # Streamlit UI: Main entry point, session state, UI layout
├── llm_advisor.py          # Gemini Backend: Enforces strict file constraints & calls API
├── audio_clips/            # 🎼 Local reference of stems (used for logic/inventory checks)
│   ├── explore/ ...        
│   ├── combat/ ...
│   └── ...                 
├── my_component/
│   ├── stem_mixer.py       # Bridge: Streamlit Python <-> React Frontend
│   └── frontend/
│       ├── src/MyComponent.tsx # React Logic: Manages Howler.js instances, Play/Stop state
│       └── ...             
├── requirements.txt        # Python dependencies
└── README.md               # Documentation
```

-----

## ⚡️ Quick Start

1.  **Install Python requirements**

    ```bash
    pip install -r requirements.txt
    ```

2.  **Configure Credentials**

      - Create a `.env` file in the root directory:
        ```
        GOOGLE_API_KEY=your_gemini_api_key_here
        ```

3.  **Build the React Frontend**
    *(Only needed if you modify the `my_component` code)*

    ```bash
    cd my_component/frontend
    npm install
    npm run build
    ```

4.  **Launch the App**

    ```bash
    streamlit run demo2_st.py
    ```

-----

## 🧩 Component Highlights

  - **`demo2_st.py`:** The "Brain." It manages the session history and displays the "Mixing Details" dashboard.
  - **`llm_advisor.py`:** The "Guardrails." It performs a `os.listdir` check before asking the LLM, ensuring the AI never recommends a file that doesn't exist.
  - **`MyComponent.tsx`:** The "Engine." A custom React component that manages the `Howl` objects. It handles the complex logic of stopping previous tracks, fading in new ones, and updating the visualizer.

-----

## 🤝 Credits

Powered by [Streamlit](https://streamlit.io), [Google Gemini](https://ai.google.com/gemini/), and [Howler.js](https://howlerjs.com/).

-----

## 📋 License

MIT. See LICENSE for details.