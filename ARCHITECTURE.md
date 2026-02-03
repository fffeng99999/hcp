# HCP Architecture

This document describes the high-level architecture of the HCP project, including system components, data flow, and module responsibilities.

## 1. High-Level Architecture

HCP consists of four main layers:

1. **Presentation Layer**: `hcp-ui` (Vue 3 frontend)
2. **Application Layer**: Backend services exposing APIs
3. **Consensus & Simulation Layer**: Consensus engine and test network
4. **Data & Analytics Layer**: Metrics collection, storage, and analysis

```text
+-----------------------------------------------------------+
|                        hcp-ui (Web UI)                    |
|  - Dashboard  - Consensus  - Benchmarks  - Metrics  ...   |
+---------------------------▲-------------------------------+
                            │ REST / WebSocket
+---------------------------▼-------------------------------+
|                 Backend API Service(s)                    |
|  - Scenario Management   - Node Control   - Metrics API   |
+---------------------------▲-------------------------------+
                            │ RPC / IPC / Network
+---------------------------▼-------------------------------+
|             Consensus & Simulation Engine                 |
|  - Consensus Algorithms (Raft, PBFT, tPBFT, HotStuff)     |
|  - Workload Generators (HFT Scenarios)                    |
|  - Network Simulator (latency, packet loss, topology)     |
+---------------------------▲-------------------------------+
                            │ Events / Logs / Metrics
+---------------------------▼-------------------------------+
|                 Data & Analytics Layer                    |
|  - Time-series Metrics Store                              |
|  - Experiment Results (CSV/JSON)                          |
|  - Reporting & Export                                     |
+-----------------------------------------------------------+
```

## 2. Frontend (hcp-ui)

### 2.1 Responsibilities

- Provide an intuitive interface to:
  - Configure consensus algorithms and parameters
  - Define and start benchmark scenarios
  - Monitor real-time metrics (TPS, latency, node status)
  - Visualize experiment results
- Communicate with backend via REST APIs and (optionally) WebSockets

### 2.2 Key Modules

- **Views**
  - `Dashboard`: Overview of current system status and key metrics
  - `Consensus`: Configuration and visualization of consensus algorithms
  - `Benchmarks`: Management of benchmark tasks and result lists
  - `Metrics`: Detailed charts of TPS, latency, resource usage
  - `Node`: Node list, roles, health, and logs
  - `System`: System-level status, version, environment
  - `Policies`: Configuration for optimization strategies and DRL policies
  - `Settings`: User preferences and basic system settings

- **Store (Pinia)**
  - Global state for user session, current scenario, and real-time data

- **API Layer (Axios)**
  - Typed API clients for backend endpoints

- **Visualization**
  - ECharts for time-series and comparative charts
  - D3.js for network topology and consensus flows

## 3. Backend API Service

*(Implementation language and framework still to be finalized.)*

### 3.1 Responsibilities

- Expose APIs for:
  - Scenario definition (workloads, node counts, network conditions)
  - Benchmark control (start, stop, pause, resume)
  - Consensus configuration (algorithm selection, parameters)
  - Node management (start/stop nodes, assign roles)
  - Metrics retrieval (current and historical)
- Orchestrate the consensus engine and simulation environment

### 3.2 Example API Endpoints

- `POST /api/scenarios` - Create a new benchmark scenario
- `POST /api/scenarios/{id}/start` - Start a scenario
- `GET  /api/scenarios/{id}/metrics` - Get metrics for a scenario
- `GET  /api/nodes` - List nodes
- `POST /api/nodes/{id}/restart` - Restart a node
- `GET  /api/system/status` - Get system health

## 4. Consensus & Simulation Engine

### 4.1 Components

- **Consensus Algorithms**
  - Baseline: Raft, PBFT
  - Optimized: tPBFT, HotStuff
  - Experimental: DRL-optimized variants, hybrid PBFT+Raft

- **Workload Generators**
  - HFT transaction patterns (order submission, cancellation, matching)
  - Burst traffic and adversarial patterns

- **Network Simulator**
  - Configurable latency, jitter, and packet loss
  - Different topologies (fully connected, clustered, etc.)

### 4.2 Data Flow (Single Scenario)

1. User defines a scenario via hcp-ui
2. Backend records the scenario and initializes nodes and consensus engine
3. Workload generator starts sending transactions
4. Consensus algorithm processes and commits transactions
5. Metrics are continuously collected and sent to the data layer
6. hcp-ui polls or subscribes to metrics and updates charts in real time

## 5. Data & Analytics Layer

### 5.1 Storage

- Time-series database or structured logs for:
  - TPS over time
  - Latency distributions
  - Resource usage per node
  - Consensus events (view changes, leader elections, etc.)

- Experiment result files (CSV/JSON) for offline analysis and thesis figures

### 5.2 Analytics

- Online analytics for:
  - Real-time dashboards
  - Alerting (e.g., if latency exceeds threshold)

- Offline analytics for:
  - Aggregated statistics (mean, p95, p99 latency)
  - Algorithm comparisons

## 6. AI & DRL Integration (Optional / Advanced)

### 6.1 Integration Points

- Policy agent adjusting:
  - Batch sizes
  - Timeouts
  - Leader/validator selection
- Reward function based on:
  - Achieved TPS
  - Latency targets
  - Stability (low variance)

### 6.2 Architecture Extension

```text
+--------------------------+
|    DRL Policy Agent      |
+------------▲-------------+
             │ Actions
+------------▼-------------+
|  Consensus Parameters    |
+--------------------------+
             ▲
             │ Metrics / Reward
             ▼
+--------------------------+
|    Metrics Collector     |
+--------------------------+
```

## 7. Deployment Topologies

### 7.1 Single-Machine Development

- All components run on a single powerful machine:
  - Multiple simulated nodes (processes or threads)
  - Local backend and hcp-ui

### 7.2 Multi-Machine / Cluster (Optional)

- Nodes distributed across several machines or VMs
- Central backend coordinating via network
- hcp-ui can be accessed from a browser on any machine

## 8. How to Use This Architecture Document

- For **developers**: Understand module boundaries and how to extend functionality
- For **researchers**: Map experiments to system components and data flows
- For **AI agents**: Use this as a reference to locate code and APIs when automating tasks within the HCP ecosystem
