# Smoke test

From the repository root:

```bash
bash tools/bootstrap.sh
bash tools/smoke.sh --output runs/smoke
```

Use a new output directory. The entry starts real RTL sessions, checks stimulus handling and feedback, and recounts the saved traces. No model account is required. Inspect the verification receipt in the output directory for the combined check result.