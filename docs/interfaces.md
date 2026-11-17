# Framework interfaces

| Function | Interface |
|---|---|
| Design knowledge | `design.knowledge.KnowledgeBase.ingest/link/query` |
| Word-level graph | `design.graph.build_graph/DesignGraph` |
| Goal decomposition | `reasoning.binding.bind_bin`, `reasoning.temporal.bind_and_decompose` |
| Probe selection | `observation.selection.ProbeRegistry.select/assignments` |
| Evidence comparison | `observation.comparison.compare/EvidenceJudge` |
| Trace windows | `observation.comparison.window/compress/expand` |
| Experience storage | `memory.records.ExperienceStore.add/find` |
| Prefix replay | `memory.records.PrefixStore.store/compatible/replay` |
| Orchestration | `engine.interfaces`, `engine.paper.run_two_pass` |
| Execution accounting | `engine.budget.BudgetLedger` |

The executable examples are in `examples/paper/`: `run_reasoning`, `run_slice`, and `run_prefix`.
