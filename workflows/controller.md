# Desktop relay controller

This workflow is intended for users who want to reproduce the experimental workflow through an ordinary subscription account while avoiding separate API calls. The desktop host must support conversation management and local command execution. Account limits and available models still apply.

## Start

Run preflight, then start the simulator in a new output directory:

```bash
bash tools/lumen.sh preflight
bash tools/run.sh --arm base --output runs/relay_base
```

In another terminal, activate the environment and prepare the public materials:

```bash
source "${LUMEN_VENV:-.venv}/bin/activate"
python -m lumen.providers.materials --arm base --output runs/materials_base
```

The main conversation is the controller. Create a fresh experiment conversation with the chosen model. The host may expose tools such as `create_thread`, `send_message_to_thread`, `wait_threads`, and `read_thread`; use the host's actual tool definitions. These tools are not Python dependencies.

## Relay loop

1. Deliver every `group_*.txt` in order and record its acknowledgement. Check the material manifest and record actual delivery.
2. Read simulator status and forward the assigned target and public feedback.
3. Obtain the experiment conversation's final response and save its complete UTF-8 text.
4. Submit that exact text to the simulator with a unique receipt path.
5. Return the actual feedback to the same experiment conversation and repeat until the simulator completes.

```bash
bash tools/lumen.sh status
bash tools/lumen.sh send --file runs/reply_001.txt --receipt runs/receipt_001.json
bash tools/lumen.sh audit --run runs/relay_base
```

Do not repair instructions, remove code fences, add stimulus, or substitute controller-written replies. Record conversation/message identifiers, material acknowledgements, response hashes, receipts, and any host context compaction.

## Evidence continuation

After a completed baseline run, activate the environment and create its seed:

```bash
python -m lumen.commands.seed --baseline runs/relay_base --output runs/evidence_seed.json
bash tools/run.sh --arm evidence --output runs/relay_evidence --seed runs/evidence_seed.json
```

Prepare evidence materials with `--arm evidence`, create a fresh experiment conversation using the same model settings, and repeat the relay loop. The seed carries the completed baseline coverage set; the new conversation receives its own public materials and current feedback.

After completion:

```bash
python -m lumen.commands.report --baseline runs/relay_base \
  --evidence runs/relay_evidence --output runs/final
```

## Interruptions

A timeout may occur after an action has executed. Check the saved receipt and simulator audit before resubmitting. Existing receipts cannot be overwritten by the submission command. A fresh simulation requires a new output directory; the runtime does not restore arbitrary CPU snapshots.

Stop and report missing tools, unavailable models, incomplete material delivery, or ambiguous execution state. Use the single [smoke entry](../examples/smoke/README.md) to check the local installation before a model experiment.