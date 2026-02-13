# HCP Consensus Performance Report
**Date:** 2026-02-13 09:13:50
**Nodes:** 12
**Total Transactions:** 1000

## 1. Executive Summary
- **Success Rate:** 1000/1000 (100.00%)
- **Total Duration:** 13.24 seconds
- **Throughput (TPS):** 75.54 tx/sec (Submission rate)
- **Average Submission Latency:** 0.1550 seconds

## 2. Transaction Analysis
- **Min Latency:** 0.0921s
- **Max Latency:** 0.2853s
- **Failures:** 0

## 3. System Resource Usage
- **Average Load (1m):** 6.44
- **Peak Memory Usage:** 7170.05 MB (Total System)

## 4. Consensus Metrics (Last 50 Blocks)
- **Sampled Blocks:** 1 to 4
- **Total Txs in Sample:** 878

## 5. Observations & Recommendations
- **Bottlenecks:** CPU/Network latency during concurrent submission.
- **Optimization:** Increase batch size or use gRPC for higher throughput.
