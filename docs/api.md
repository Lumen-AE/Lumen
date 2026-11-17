# Model API transport

`python -m lumen.commands.api` connects an OpenAI-compatible Chat Completions service to the RTL simulator. It sends the public materials, preserves continuous history, and forwards replies verbatim. The model identifier is selected explicitly for the API service.

## Run

```bash
source "${LUMEN_VENV:-.venv}/bin/activate"
read -rsp 'API key: ' OPENAI_API_KEY; export OPENAI_API_KEY; echo
export LUMEN_API_MODEL='your-available-api-model'
python -m lumen.commands.api --arm base --model "$LUMEN_API_MODEL" \
  --output runs/api_base
```

Use `--base-url` and `--key-env` for another compatible service. The base URL includes its service prefix, such as `/v1`. Optional inference settings are sent only when requested; use `--help` for the supported arguments.

The controller starts the RTL process itself. Use a new output directory and an unused bind address. Keys are read from the named environment variable and are not written to experiment artifacts.

After baseline completes:

```bash
python -m lumen.commands.seed --baseline runs/api_base/simulation --output runs/api_seed.json
python -m lumen.commands.api --arm evidence --model "$LUMEN_API_MODEL" \
  --output runs/api_evidence --seed runs/api_seed.json
python -m lumen.commands.report --baseline runs/api_base/simulation \
  --evidence runs/api_evidence/simulation --output runs/api_final
unset OPENAI_API_KEY
```

Keep the same service, model, and inference options for the continuation. Seed generation requires a completed experiment. The coverage contract is independent of provider selection.

## Records and interruptions

The output directory contains provider settings, the material manifest, message history, raw replies, feedback, and a simulator subdirectory. Available usage comes from the service response; unavailable fields remain absent.

Service failures stop the controller with its journal intact. Requests are not retried automatically. A malformed textual action is submitted unchanged and handled by the simulator's action contract. If a simulator acknowledgement is missing, inspect its controller audit before resubmitting.

The API protocol and real RTL integration can be checked locally:

```bash
python -m tests.api_run --output runs/api_check
```

The check uses a local HTTP fixture and the RTL simulator.