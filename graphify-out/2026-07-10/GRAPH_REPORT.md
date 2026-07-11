# Graph Report - Fintan  (2026-07-10)

## Corpus Check
- 49 files · ~22,093 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 288 nodes · 522 edges · 26 communities (20 shown, 6 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 13 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `8fcc92f5`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Community 0
- Community 1
- Community 2
- Community 3
- Community 4
- Community 5
- Community 6
- Community 7
- Community 8
- Community 9
- Community 10
- Community 11
- Community 13
- graphify reference: extra exports and benchmark
- graphify reference: query, path, explain
- graphify reference: add a URL and watch a folder
- graphify reference: commit hook and native CLAUDE.md integration
- graphify reference: incremental update and cluster-only
- graphify reference: GitHub clone and cross-repo merge
- graphify reference: transcribe video and audio
- AGENTS.md
- extraction-spec.md

## God Nodes (most connected - your core abstractions)
1. `cmd_trading()` - 21 edges
2. `build_parser()` - 20 edges
3. `can_generate_signal()` - 15 edges
4. `welford_zscore()` - 13 edges
5. `What You Must Do When Invoked` - 12 edges
6. `generate_inputs_batch()` - 11 edges
7. `/graphify` - 10 edges
8. `read_data()` - 10 edges
9. `generate_training_files()` - 10 edges
10. `_print_json()` - 9 edges

## Surprising Connections (you probably didn't know these)
- `cmd_symbols()` --calls--> `ensure_no_duplicates()`  [EXTRACTED]
  fintan_cli.py → main.py
- `cmd_symbols()` --calls--> `find_duplicate_symbols()`  [EXTRACTED]
  fintan_cli.py → main.py
- `cmd_fetch_history()` --calls--> `generate_historical_file()`  [EXTRACTED]
  fintan_cli.py → historical_file_generator.py
- `cmd_generate_training()` --calls--> `generate_training_files()`  [EXTRACTED]
  fintan_cli.py → training_file_generator.py
- `cmd_pipeline()` --calls--> `generate_historical_file()`  [EXTRACTED]
  fintan_cli.py → historical_file_generator.py

## Import Cycles
- None detected.

## Communities (26 total, 6 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.11
Nodes (28): generate_inputs_batch(), welford_mean_std(), welford_zscore(), can_generate_signal(), OnlineStatsTest, generate_atr_batch(), generate_atr_signals(), Scan `batch_size` consecutive intervals starting at `start_index`, filter by (+20 more)

### Community 1 - "Community 1"
Cohesion: 0.08
Nodes (48): ArgumentParser, get_account(), get_asset(), get_assets(), get_option(), get_options(), cancel_all_orders(), cancel_order() (+40 more)

### Community 2 - "Community 2"
Cohesion: 0.11
Nodes (12): get_historical_bars(), get_historical_quotes(), fetch_bar(), fetch_quote(), generate_historical_file(), generate_historical_file_batch(), log_progress(), Any (+4 more)

### Community 3 - "Community 3"
Cohesion: 0.14
Nodes (23): Event, cmd_labels(), cmd_shuffle(), generate_labels(), generate_labels_batch(), Lock, ensure_no_duplicates(), find_duplicate_symbols() (+15 more)

### Community 4 - "Community 4"
Cohesion: 0.08
Nodes (24): For /graphify add and --watch, For /graphify query, For the commit hook and native CLAUDE.md integration, For --update and --cluster-only, /graphify, Honesty Rules, Interpreter guard for subcommands, Part A - Structural extraction for code files (+16 more)

### Community 5 - "Community 5"
Cohesion: 0.15
Nodes (14): buy_limit_order(), buy_market_order(), cover_short(), place_bracket_order(), place_trailing_stop_order(), Short a given symbol and quantity.     Input parameters: symbol: str, qty: int,, Cover a short position for a given symbol and quantity.     Input parameters: sy, Place a trailing stop order for a given symbol, quantity, and trail price.     I (+6 more)

### Community 6 - "Community 6"
Cohesion: 0.36
Nodes (7): aggregate_trades_with_quotes(), calculate_aggression_metrics(), calculate_stat_metrics(), generate_interval_metrics(), generate_interval_metrics_update(), DataFrame, datetime

### Community 7 - "Community 7"
Cohesion: 0.29
Nodes (8): calculate_ema(), calculate_ema_update(), generate_macd_signals(), generate_macd_signals_update(), DataFrame, Series, Update the MACD signals in a given MACD DataFrame by processing the last data po, Generate an MACD signal DataFrame for a given data series.     Input parameters:

### Community 8 - "Community 8"
Cohesion: 0.43
Nodes (3): load_config(), _set_nested(), AppConfigTest

### Community 9 - "Community 9"
Cohesion: 0.32
Nodes (6): generate_bollinger_signals(), generate_bollinger_signals_update(), DataFrame, Series, Generate a bollinger signal DataFrame for a given data series.     Input paramet, Update the bollinger signals in a given bollinger DataFrame by processing the la

### Community 10 - "Community 10"
Cohesion: 0.32
Nodes (6): generate_rsi_signals(), generate_rsi_signals_update(), DataFrame, Series, Generate an RSI signal DataFrame for a given data series.     Input parameters:, Update the RSI signals in a given RSI DataFrame by processing the last data poin

### Community 17 - "graphify reference: extra exports and benchmark"
Cohesion: 0.22
Nodes (8): graphify reference: extra exports and benchmark, Step 6b - Wiki (only if --wiki flag), Step 7 - Neo4j export (only if --neo4j or --neo4j-push flag), Step 7a - FalkorDB export (only if --falkordb or --falkordb-push flag), Step 7b - SVG export (only if --svg flag), Step 7c - GraphML export (only if --graphml flag), Step 7d - MCP server (only if --mcp flag), Step 8 - Token reduction benchmark (only if total_words > 5000)

### Community 18 - "graphify reference: query, path, explain"
Cohesion: 0.33
Nodes (5): For /graphify explain, For /graphify path, graphify reference: query, path, explain, Step 0 — Constrained query expansion (REQUIRED before traversal), Step 1 — Traversal

### Community 19 - "graphify reference: add a URL and watch a folder"
Cohesion: 0.50
Nodes (3): For /graphify add, For --watch, graphify reference: add a URL and watch a folder

### Community 20 - "graphify reference: commit hook and native CLAUDE.md integration"
Cohesion: 0.50
Nodes (3): For git commit hook, For native CLAUDE.md integration, graphify reference: commit hook and native CLAUDE.md integration

### Community 21 - "graphify reference: incremental update and cluster-only"
Cohesion: 0.50
Nodes (3): For --cluster-only, For --update (incremental re-extraction), graphify reference: incremental update and cluster-only

## Knowledge Gaps
- **43 isolated node(s):** `Usage`, `What graphify is for`, `Step 0 - GitHub repos and multi-path merge (only if a URL or several paths)`, `Step 1 - Ensure graphify is installed`, `Step 2 - Detect files` (+38 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `generate_inputs_batch()` connect `Community 0` to `Community 1`, `Community 3`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Why does `build_parser()` connect `Community 1` to `Community 3`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **Are the 11 inferred relationships involving `build_parser()` (e.g. with `cmd_fetch_history()` and `cmd_generate_training()`) actually correct?**
  _`build_parser()` has 11 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Usage`, `What graphify is for`, `Step 0 - GitHub repos and multi-path merge (only if a URL or several paths)` to the rest of the system?**
  _74 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.11498257839721254 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.08469449485783424 - nodes in this community are weakly interconnected._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.11330049261083744 - nodes in this community are weakly interconnected._