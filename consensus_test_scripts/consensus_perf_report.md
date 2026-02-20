# HCP Consensus Performance Report
**Date:** 2026-02-13 10:14:08
**Nodes:** 16
**Total Transactions:** 10

## 1. Executive Summary
- **Success Rate:** 10/10 (100.00%)
- **Total Duration:** 0.27 seconds
- **Throughput (TPS):** 36.60 tx/sec (Submission rate)
- **Average Submission Latency:** 0.2059 seconds

## 2. Transaction Analysis
- **Min Latency:** 0.1723s
- **Max Latency:** 0.2223s
- **Failures:** 0

## 3. System Resource Usage
- **Average Load (1m):** 7.44
- **Peak Memory Usage:** 6982.68 MB (Total System)

## 4. Consensus Metrics (Last 50 Blocks)
- **Sampled Blocks:** 1 to 2
- **Total Txs in Sample:** 0

## 5. Observations & Recommendations
- **Bottlenecks:** CPU/Network latency during concurrent submission.
- **Optimization:** Increase batch size or use gRPC for higher throughput.
