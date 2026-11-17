# Lumen

Lumen is a graph-guided framework for LLM-driven RTL functional coverage closure. It represents synthesizable RTL and coverage-monitor logic in a unified word-level circuit graph. The graph connects coverage predicates to temporal milestones, bounded internal-state evidence, and reusable reset-anchored input prefixes.

The workflow has an offline construction stage and an online closure loop. Offline analysis builds the graph and binds coverage definitions. Online scheduling, stimulus generation, cycle-accurate execution, evidence auditing, and verified prefix reuse guide the model toward remaining coverage targets.

This repository contains the framework implementation, DUT sources, configuration, examples, and launch scripts used for the paper's open-source RTL study. Model integration is available through an OpenAI-compatible API or an interactive desktop relay; the relevant guides are in `docs/` and `workflows/`.

## Repository layout

| Directory | Purpose |
|---|---|
| `src/lumen/` | Core graph, reasoning, observation, execution, and model-provider modules |
| `targets/` | DUT sources, coverage definitions, and simulation adapters |
| `profiles/` | Experiment and DUT configuration |
| `examples/` | Runnable framework examples |
| `tests/` | Unit and integration checks |
| `tools/` | Environment setup, launchers, and source checks |
| `docs/` | Architecture, interfaces, and API guides |
| `workflows/` | Model and desktop-relay usage guides |
| `licenses/` | Bundled license texts |

## Quick start

Use Linux or WSL with Python 3.10+, Verilator, and a C++ compiler:

```bash
bash tools/bootstrap.sh
bash tools/lumen.sh preflight
bash tools/smoke.sh --output runs/smoke
```

For API-backed model use, configure an OpenAI-compatible endpoint and follow [docs/api.md](docs/api.md). For reproduction through a subscription-based desktop conversation relay, follow [workflows/controller.md](workflows/controller.md).

## Reference

Lumen: *Graph-Guided Temporal Reasoning for LLM-Driven RTL Functional Coverage Closure*.

## Acknowledgments

Parts of the experimental environment were informed by [LLM4DV](https://github.com/ZixiBenZhang/ml4dv) and GoGoTB. Their original licenses and notices remain with the relevant files.

## License

Lumen contributions are licensed under the [Apache License 2.0](LICENSE). Bundled DUTs retain their original copyright notices and applicable licenses.
