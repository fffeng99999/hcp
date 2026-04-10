# HCP - High-Frequency Trading Consensus Performance Analysis Framework

**High-frequency trading Consensus Performance (HCP)** is an undergraduate graduate thesis project focused on analyzing the performance boundaries and optimization strategies of blockchain consensus mechanisms under high-frequency trading (HFT) scenarios.

## 📋 Project Overview

### What is HCP?

HCP is a comprehensive performance evaluation framework and distributed ecosystem designed to:

1. **Analyze Consensus Limits**: Study the performance boundaries of various blockchain consensus algorithms (tPBFT, Raft, HotStuff) when subjected to high-frequency trading workloads
2. **Benchmark Performance**: Measure throughput (TPS), latency, fault tolerance, and resource consumption across different consensus mechanisms
3. **Optimize Strategies**: Explore optimization techniques including:
   - Trust-based dynamic node selection (tPBFT)
   - High-throughput protocols (Leios)
   - Deep Reinforcement Learning (DRL) for adaptive consensus adjustment
   - Hybrid consensus mechanisms
4. **Evaluate Trade-offs**: Quantify the scalability-security-efficiency trilemma in blockchain systems

### Key Metrics

- **Target Environment**: 50-200 nodes consortium blockchain
- **Latency Goal**: ≤500ms transaction finality
- **Workload**: High-frequency financial transactions
- **Primary Focus**: Consensus algorithm performance and optimization

## �️ Dual-Mode Architecture

The HCP ecosystem is structured into two distinct operating paradigms, allowing researchers to choose between rapid local prototyping and comprehensive microservice integration.

### 1. Small Environment Experimental Testing (Lab Mode)
Designed for rapid iteration, algorithm benchmarking, and local performance analysis.
- **[hcp]**: Main project documentation and scripts orchestration.
- **[hcp-consensus]**: The core consensus engine (tPBFT based on Cosmos-SDK/CometBFT).
- **[hcp-loadgen]**: High-performance transaction load generator written in Rust.
- **[hcp-lab]**: Python-based experiment orchestration, metric collection, and analysis.

### 2. Large-Scale Integrated System (Production Mode)
A full-fledged microservices architecture for large-scale deployment, real-time monitoring, and complete system testing. Includes the core engines from the Lab Mode (`hcp`, `hcp-consensus`, `hcp-loadgen`), augmented by:
- **[hcp-ui]**: Frontend visualization dashboard (Vue 3).
- **[hcp-server]**: Backend API service for data retrieval and configuration.
- **[hcp-gateway]**: API gateway service for routing and access control.
- **[hcp-antimanip]**: Anti-manipulation mechanism module for network security.
- **[hcp-deploy]**: Deployment configurations and orchestration scripts (Docker/Kubernetes).

### System Components

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        HCP Project Ecosystem                           │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  [ Large-Scale Integrated System ]       [ Experimental Lab Mode ]     │
│                                                                        │
│  ┌────────────┐   ┌────────────┐        ┌────────────┐ ┌────────────┐  │
│  │   hcp-ui   │◄─►│hcp-gateway │        │  hcp-lab   │ │ hcp-deploy │  │
│  └────────────┘   └────────────┘        └────────────┘ └────────────┘  │
│                         ▲                     │              │         │
│                         ▼                     ▼              ▼         │
│  ┌────────────┐   ┌────────────┐        ┌────────────┐ ┌────────────┐  │
│  │hcp-antimanip◄─►│ hcp-server │◄──────►│hcp-loadgen │ │    hcp     │  │
│  └────────────┘   └────────────┘        └────────────┘ └────────────┘  │
│                         ▲                     │              │         │
│                         ▼                     ▼              ▼         │
│                   ┌────────────┐        ┌────────────┐                 │
│                   │ Database / │◄──────►│hcp-consensus                 │
│                   │ Prometheus │        │(tPBFT/Cosmos)                │
│                   └────────────┘        └────────────┘                 │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

## 📊 Consensus Algorithms Evaluated

### Primary Algorithms

1. **tPBFT (Trust-based PBFT)**
   - Enhanced PBFT with dynamic node selection
   - Equity scoring for node trust
   - Optimized for consortium blockchains
   - Better scalability beyond 30 nodes

2. **Raft**
   - Leader-based consensus
   - Strong consistency guarantees
   - Lower overhead than PBFT

3. **HotStuff**
   - Modern BFT consensus
   - Better scalability
   - Robust under Byzantine conditions

## 📈 Performance Metrics

### Key Indicators

| Metric | Target | Description |
|--------|--------|-------------|
| Throughput (TPS) | 1,000+ | Transactions per second |
| Latency | ≤500ms | Transaction finality time |
| Fault Tolerance | >33% | Byzantine fault tolerance |
| CPU Usage | Minimized | Resource efficiency |
| Network Bandwidth | Optimized | Communication overhead |
| Finality Time | <1s | Time to reach finality |
| Scalability | 50-200 nodes | Nodes in consortium |

## 🔄 Technology Stack

The project spans across multiple languages tailored to their specific domains:

- **Consensus Engine**: Go, Cosmos-SDK, CometBFT
- **Load Generator**: Rust, Tokio, gRPC/HTTP
- **Experiment Orchestration**: Python, Pandas, Matplotlib
- **Frontend (UI)**: Vue 3, TypeScript, Vite, Element Plus, ECharts
- **Backend Services**: Go / Node.js
- **Deployment**: Docker, Kubernetes, Shell Scripts

## 🚀 Getting Started

Because the HCP ecosystem is distributed across multiple repositories, your starting point depends on your testing goals.

### For Small Environment Experimental Testing (Lab Mode)

```bash
# 1. Clone the orchestration and core repos
git clone https://github.com/fffeng99999/hcp.git
git clone https://github.com/fffeng99999/hcp-consensus.git
git clone https://github.com/fffeng99999/hcp-loadgen.git
git clone https://github.com/fffeng99999/hcp-lab.git

# 2. Follow instructions in hcp-lab to run local experiments
cd hcp-lab
pip install -r requirements.txt
python run_experiment.py
```

### For Large-Scale Integrated System

```bash
# 1. Clone the deployment repository
git clone https://github.com/fffeng99999/hcp-deploy.git
cd hcp-deploy

# 2. Use the deployment scripts to spin up the entire ecosystem
# This will pull and orchestrate hcp-server, hcp-gateway, hcp-ui, etc.
./start_cluster.sh
```

## 🔬 Research Context

### Background

Blockchain consensus mechanisms face significant challenges when supporting high-frequency financial transactions. Traditional consensus algorithms (PoW, PoS) suffer from:

1. **High Latency**: Unsuitable for HFT requiring sub-second finality
2. **Limited Throughput**: Cannot handle thousands of transactions per second
3. **Resource Inefficiency**: Excessive computational and network overhead
4. **Scalability Issues**: Performance degrades rapidly with node count

### Methodology

The HCP project employs:

1. **Literature Review**: Analysis of 200+ academic publications
2. **Algorithmic Implementation**: Implementation of multiple consensus variants (e.g., tPBFT via `hcp-consensus`)
3. **Experimental Evaluation**: Benchmarking with realistic HFT workloads via `hcp-loadgen`
4. **Optimization Development**: Proposing enhancements like the `hcp-antimanip` module
5. **Performance Analysis**: Quantifying trade-offs and scalability limits orchestrated by `hcp-lab`

## 🎓 Academic Context

- **Institution**: Chengdu University of Information Technology
- **Department**: School of Computer Science
- **Project Type**: Undergraduate Graduate Thesis
- **Duration**: 18 weeks (planned)

## 🤝 Contributing

This is an academic research project. Contributions, feedback, and research discussions are welcome.

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.

## 📧 Contact

- GitHub: [@fffeng99999](https://github.com/fffeng99999)

## 🔗 Ecosystem Repositories

The HCP project is modularized into the following repositories based on functionality:

### Small Environment Experimental Testing
- [hcp](https://github.com/fffeng99999/hcp) - Main project documentation and scripts orchestration
- [hcp-consensus](https://github.com/fffeng99999/hcp-consensus) - Consensus engine (tPBFT based on Cosmos-SDK/CometBFT)
- [hcp-loadgen](https://github.com/fffeng99999/hcp-loadgen) - High-performance Rust load generator for transactions
- [hcp-lab](https://github.com/fffeng99999/hcp-lab) - Python experiment orchestration, monitoring and analysis

### Large-Scale Integrated System
*(Includes the core testing modules above, plus the following for a complete ecosystem)*
- [hcp-ui](https://github.com/fffeng99999/hcp-ui) - Frontend visualization dashboard
- [hcp-server](https://github.com/fffeng99999/hcp-server) - Backend API service
- [hcp-gateway](https://github.com/fffeng99999/hcp-gateway) - API gateway service
- [hcp-deploy](https://github.com/fffeng99999/hcp-deploy) - Deployment configurations and scripts
- [hcp-antimanip](https://github.com/fffeng99999/hcp-antimanip) - Anti-manipulation mechanism module

---

**Last Updated**: April 2026
**Version**: 1.1.0
