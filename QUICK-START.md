# HCP Quick Start

This guide helps you quickly understand and run the HCP project when you clone the `hcp` repository alongside other projects.

## 1. Repository Layout

When you clone `hcp`, you typically have a structure like:

```text
workspace/
├── hcp/        # This repo (meta + docs + pointers)
├── hcp-ui/     # Frontend (from https://github.com/fffeng99999/hcp-ui)
├── ...other projects...
```

The `hcp` repo mainly contains **documentation and high-level design**, while `hcp-ui` and future repos (e.g., `hcp-core`, `hcp-benchmark`) contain the actual code.

## 2. What to Read First

1. `README.md`
   - Overall introduction of the HCP project
   - Architecture, goals, and research background

2. `PROJECT-VALUE.md`
   - Why this project exists
   - Academic and practical value

3. `ARCHITECTURE.md`
   - High-level system design
   - Main components and data flow

4. `TECHNICAL-ROADMAP.md`
   - Development plan
   - Phases and milestones

After reading these four files, you should **clearly know**:

- What HCP is trying to solve
- How the system is roughly structured
- What has been implemented and what is planned

## 3. How to Run the UI (hcp-ui)

### 3.1 Clone Repositories

```bash
# In your workspace directory

git clone https://github.com/fffeng99999/hcp.git
git clone https://github.com/fffeng99999/hcp-ui.git
```

### 3.2 Install Dependencies & Run Dev Server

```bash
cd hcp-ui
npm install
npm run dev
```

Then open the printed local URL (e.g., `http://localhost:5173`) in your browser.

> Note: Backend APIs and consensus engine are still under development. Some pages may use mock data or partial functionality.

## 4. For AI Agents / Tools

If you are using AI tools (like GitHub Copilot Agents) to understand or modify this project:

- Use `README.md` to get the **project context**
- Use `ARCHITECTURE.md` to locate **which layer** you should work in
- Use `TECHNICAL-ROADMAP.md` to know **what is planned next**
- Use `PROJECT-VALUE.md` to keep changes aligned with **project goals**

## 5. Typical Workflows

### 5.1 As a Developer

1. Read `README.md` and `ARCHITECTURE.md`
2. Run `hcp-ui` locally
3. Implement or modify frontend features under `src/views` or `src/components`
4. (Later) Integrate with backend APIs when available

### 5.2 As a Researcher/Student

1. Read `README.md`, `PROJECT-VALUE.md`, and `TECHNICAL-ROADMAP.md`
2. Identify which consensus algorithm or scenario you are interested in
3. Extend or design experiments based on the roadmap
4. Use HCP-UI to visualize and present results

## 6. Status

As of February 2026:

- `hcp` repo contains project documentation and planning
- `hcp-ui` repo contains the initial version of the Vue 3 frontend
- Backend and consensus engine are in planning/early implementation stage

You can track progress and changes via commit history and `TECHNICAL-ROADMAP.md`.
