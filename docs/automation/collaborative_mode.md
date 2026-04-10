# Collaborative Interactive Mode

The **Collaborative Interactive Mode** allows human operators and the AI agent to work together in a shared, visible browser session. This mode is ideal for discovering new portals, troubleshooting extraction, or handling complex filters that require human judgment.

## Key Features

1.  **Visible Browser**: The agent opens a visible window (via BrowserOS or Crawl4AI) that both the agent and human can see and interact with.
2.  **Visual Highlighting**: The agent highlights elements it interacts with (e.g., green glow for successful clicks/fills) to provide real-time feedback.
3.  **Real-Time Recording**: All interactions (agent-driven or human-driven) are captured into a raw trace using the `AriadneRecorder`.
4.  **Trace Promotion**: Recorded discovery sessions can be promoted into permanent `search.json` or `easy_apply.json` maps.

## Usage

To start a collaborative discovery session:

```bash
# Example: Search for ML Engineer jobs on XING with visible feedback and recording
python -m src.automation.main scrape --source xing --interactive --visible --record --backend browseros --job-query "ML Engineer" --city "Berlin"
```

### CLI Flags
-   `--interactive`: Triggers the UI-based discovery flow instead of static URL generation.
-   `--visible`: Forces the browser to open in a visible window.
-   `--record`: Initializes the `AriadneRecorder` to capture the session.
-   `--backend <crawl4ai|browseros>`: Chooses the execution motor.

## Collaborative Workflow

1.  **Agent Start**: The agent navigates to the portal and performs initial actions defined in the `search.json` map (e.g., entering keywords).
2.  **Human Interjection**: Since the window is visible, the human operator can click additional filters or resolve CAPTCHAs while the session is active.
3.  **Recording**: Every action is logged to `data/ariadne/recordings/rec_<portal>_<timestamp>/`.
4.  **Agent Finish**: Once the search results are reached, the agent captures the final URL and proceeds with extraction.

## Future Roadmap
-   **Glow Pointer**: Agent will "point" to elements before interacting.
-   **Voice/Text Feedback**: Integrated chat within the visible browser.
-   **Direct Selection**: Human can click an element to "point" it out to the agent for future map generation.
