# Lumen

Lumen is a graph-guided framework for LLM-driven RTL functional coverage closure. It represents synthesizable RTL and coverage-monitor logic in a unified word-level circuit graph. The graph connects coverage predicates to temporal milestones, bounded internal-state evidence, and reusable reset-anchored input prefixes.

## Capabilities

- Index and link design documents, RTL, instruction descriptions, and coverage definitions.
- Build word-level design graphs and decompose coverage goals into bounded temporal conditions.
- Select read-only probes, inspect execution evidence, and refine observation when more context is needed.
- Store execution experience and replay compatible preparation prefixes.
- Coordinate generation, simulation, coverage feedback, and execution records through replaceable interfaces.
- Run model-driven experiments through either an API or a desktop dialogue relay.

The reference simulation workflow uses Ibex and offers ordinary feedback (`base`) and feedback with target-related observations (`evidence`). The analysis and reuse modules have separate executable examples and can be integrated through the framework interfaces. DUT sources are organized under `targets/`.

## Repository layout

| Directory | Contents |
|---|---|
| `src/lumen/` | Core framework: execution, coverage, design knowledge, reasoning, observation, memory, providers, and commands |
| `targets/` | DUT sources, supporting resources, coverage definitions, and simulation adapters |
| `profiles/` | DUT and experiment configuration |
| `workflows/` | Model instructions and desktop relay guides |
| `examples/` | Smoke-test guidance and executable framework examples |
| `tests/` | Unit tests, RTL integration checks, and replay regression |
| `tools/` | Environment setup, launchers, and source verification |
| `docs/` | Module overview, framework interfaces, and API usage |
| `licenses/` | Third-party license texts |

## Installation

Use Linux or WSL with Python 3.10+, GNU Make, a C++ compiler, and Verilator. From the repository root:

```bash
bash tools/bootstrap.sh
bash tools/lumen.sh preflight
```

The installer creates `.venv/`. Set `LUMEN_VENV` before installation to use another location. Keep the complete source checkout: the Python package loads RTL and configuration from the same tree. Runtime outputs and build caches stay local.

## Smoke test

Run the self-contained smoke test to check the simulator, stimulus transport, feedback, and coverage recount:

```bash
bash tools/smoke.sh --output runs/smoke
```

It requires no model account. Use a new output directory for each run. Successful completion writes a verification receipt in that directory.

## Model API

Activate the environment and select a model available through your API provider:

```bash
source "${LUMEN_VENV:-.venv}/bin/activate"
read -rsp 'API key: ' OPENAI_API_KEY; export OPENAI_API_KEY; echo
export LUMEN_API_MODEL='your-available-api-model'
python -m lumen.commands.api --arm base \
  --model "$LUMEN_API_MODEL" --output runs/api_base
```

The controller starts the simulator, sends the public design materials, maintains the conversation, and forwards model replies to RTL. OpenAI-compatible Chat Completions services can be configured with `--base-url` and `--key-env`. See the [API guide](docs/api.md) for continuation with evidence feedback and output handling.

## Desktop dialogue relay

This route is intended for testers who are sensitive to API costs. It lets users reproduce the paper's experimental workflow with an ordinary subscription account through a desktop application that supports conversations and local tools, without separate API requests for the relay. Available models and usage limits depend on the account and host application.

One main conversation acts as the controller and creates a separate experiment conversation. The controller runs the simulator and forwards materials and feedback; the experiment conversation generates stimulus. The controller preserves the model's replies verbatim and returns the simulator's feedback to the same experiment conversation.

```bash
bash tools/run.sh --arm base --output runs/relay_base
```

In another terminal, prepare the materials:

```bash
source "${LUMEN_VENV:-.venv}/bin/activate"
python -m lumen.providers.materials --arm base --output runs/materials
```

Follow the [controller guide](workflows/controller.md), or paste the [controller starter](workflows/start_controller.md) into the main conversation. The guide covers material delivery, literal reply submission, evidence continuation, and recovery from interruptions. Conversation-management tools are supplied by the desktop application.

## Framework examples

Install the optional analysis dependencies, then run the examples:

```bash
bash tools/bootstrap_paper.sh
source "${LUMEN_VENV:-.venv}/bin/activate"
python -m examples.paper.run_reasoning --output runs/reasoning
python -m examples.paper.run_slice --reasoning runs/reasoning --output runs/observation
python -m examples.paper.run_prefix --output runs/prefix
```

These examples exercise knowledge indexing, RTL graph construction, temporal decomposition, probe generation, evidence comparison, and prefix reuse. See [framework interfaces](docs/interfaces.md) and [module overview](docs/architecture.md).

## Validation

With the optional analysis dependencies installed:

```bash
source "${LUMEN_VENV:-.venv}/bin/activate"
python -m unittest discover -s tests -p 'test_*.py' -v
```

`SOURCE_MANIFEST.json` records file hashes; after intentional source edits, refresh it with `python tools/seal.py --write` before running preflight.

## Acknowledgments

The initial experimental environment for running **Ibex/lowRISC** in Lumen was adapted from [LLM4DV](https://github.com/ZixiBenZhang/ml4dv) by Zixi Zhang and contributors. Lumen's mechanisms were subsequently added as modules built on this working experimental environment. Code from GoGoTB was also adapted to support comparative experiments with GoGoTB. We thank the authors of **LLM4DV** and **GoGoTB** for releasing or providing their source code.

## License and attribution

Lumen's original contributions are licensed under [Apache License 2.0](LICENSE). The reused LLM4DV components are also licensed under Apache License 2.0. Bundled third-party DUTs retain their own licenses and copyright notices; the separate SM4 source asset is licensed under GPL-3.0. See the original source headers and bundled license files for attribution and applicable terms. Optional Yosys/YoWASP and Z3 dependencies are installed separately under their own licenses.
