# semantic_map_ui

Live top-down semantic map viewer for the robot. Shows an occupancy grid, lidar halo, landmarks, and robot pose — fed by `semantic_bridge` over HTTP and WebSocket.

## Setup

```bash
cd semantic_map_ui
npm install
```

Copy the env file and point it at your backend:

```bash
cp .env.example .env
# Edit VITE_BACKEND_URL if your backend is not on localhost:8000
```

## Run

```bash
npm run dev        # dev server on http://localhost:3000
npm run build      # production build → dist/
npm run preview    # serve the production build locally
```

## Test

```bash
npm run test         # run all tests once
npm run test:watch   # watch mode
npm run typecheck    # TypeScript type check only
```

## Backend contract

The UI talks to `semantic_bridge`:

| Endpoint | Purpose |
|----------|---------|
| `GET /api/health` | Connection status, landmark count, robot pose |
| `GET /api/map` | Occupancy grid (fetched once on load) |
| `POST /api/clear` | Clear semantic memory |
| `WS /ws/state` | Live robot pose + landmarks + lidar scan (~5 Hz) |
| `WS /ws/camera` | JPEG frames (~10 fps) |

Set `VITE_BACKEND_URL` to override the default `http://localhost:8000`.

## Mock mode

Start the backend with `SEMANTIC_BRIDGE_MOCK=1`. The UI detects `"mock": true` in the `/api/health` response and shows a **MOCK** badge in the status panel — no other behaviour changes.

## Keyboard shortcuts

| Key | Action |
|-----|--------|
| `R` | Reset map view |
| `F` | Toggle follow-robot |
| `C` | Clear semantic memory (with confirm) |

## Project layout

```
src/
  api/            HTTP client + reconnecting WebSocket manager
  state/          Zustand store + TypeScript types
  components/
    Map/          Canvas + coordinate math + per-layer draw functions
    CameraPanel   JPEG feed + status + clear button
    ConnectionBanner  yellow/red banners for WS/ROS state
  utils/          classLabel→colour, base64→OffscreenCanvas
tests/            Unit tests (Vitest + RTL); no pixel-level canvas tests
```
