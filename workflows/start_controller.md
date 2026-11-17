# Controller starter

Paste the following into a desktop main conversation with local command and conversation-management tools. Replace the checkout, output paths, and model selection.

> The Lumen checkout is at `/absolute/path/to/Lumen`. Act as the experiment controller. Run preflight and start a baseline run in a fresh output directory. Create a separate experiment conversation with my selected model; creating that conversation is authorized for this experiment.
>
> Package the public materials with `python -m lumen.providers.materials --arm base --output ...`. Deliver every material group verbatim and wait for its acknowledgement. After confirming complete delivery, obtain the real simulator status and send the assigned target.
>
> The experiment conversation generates only literal stimulus JSON and uses no tools. Preserve every final response exactly as UTF-8 text. Submit it with `lumen send --file ... --receipt ...`, record message identifiers and receipts, and return real feedback to the same conversation. Keep its context continuous across targets.
>
> When baseline completes, create its seed and start the evidence continuation in a fresh output directory. Create a fresh experiment conversation with the same model settings, deliver the evidence materials, and repeat the relay loop. Audit the outputs and produce the final report after completion.
>
> Use the ordinary subscription conversation route for model interaction. Do not repair or replace experiment replies. If tools, model access, material delivery, or execution state prevent progress, preserve the records and report the problem.

Detailed commands and interruption handling are in the [controller guide](controller.md). For an installation check, use `bash tools/smoke.sh --output runs/smoke`.