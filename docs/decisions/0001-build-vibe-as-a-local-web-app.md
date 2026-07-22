# Build VIBE as a local web app on Node/TypeScript

**Status:** accepted
**Date:** 2026-07-22
**Deciders:** Liam Lee

## Context

VIBE needs a multi-pane workspace that spawns and renders interactive agent
CLI sessions (PTYs), plus a setup wizard and learning dashboard. The form
factor (desktop app, tmux wrapper, web app) and stack determine distribution
cost, Windows support, and how fast the team can iterate.

## Decision

Build VIBE as a **local web app**: a Node.js/TypeScript backend that spawns
PTYs via `node-pty`, and a browser frontend rendering them with `xterm.js`.
Drag-and-drop pane layout uses **Dockview** as the leading candidate. One
command (planned `vibe ui`) starts the server and opens the browser.
TypeScript end-to-end.

## Alternatives considered

- **Rust backend** — rejected: slower development for this team, and the
  single-binary benefit isn't needed yet. Would revisit if distribution pain
  demands one binary — even then, wrap the existing frontend in Tauri rather
  than rewrite.
- **Python backend** — rejected: weak PTY support on Windows and painful
  distribution.
- **Desktop-first app (Electron/Tauri)** — rejected for now: adds packaging
  overhead before product value is proven; the web frontend can be wrapped in
  Tauri later without change.
- **tmux wrapper** — rejected: can't deliver the setup wizard or learning
  dashboard, and excludes non-tmux users.

## Consequences

**Better:**

- One language (TypeScript) across backend, frontend, and future CLI.
- Browser UI gives free rich layout (Dockview), no packaging step during
  development.
- Tauri remains available later at low cost, frontend unchanged.

**Worse:**

- `node-pty` is a native module — platform-specific builds complicate `npm`
  distribution.
- A local server + browser is a heavier baseline than a pure terminal tool.

**Must now be true:**

- PTY processes are owned by the Node backend only; browser code never spawns
  or owns processes — it talks to the server over WebSocket.
- Frontend code must not depend on Node APIs, so it stays wrappable by Tauri.

## Revisit if

The HTTP-framework gate in Phase 2 surfaces a WebSocket/TypeScript blocker, or
distribution feedback shows the local-server model is a real adoption barrier.
