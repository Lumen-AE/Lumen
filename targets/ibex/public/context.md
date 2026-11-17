# Public experiment contract

The supplied protocol describes the active DUT parameters, action budget, address layout, and instruction-category encodings. Coverage is counted as the cumulative union of distinct catalog bin identities. PMP region instances have separate identities. The catalog remains fixed throughout a run.

Return a literal JSON object using the fields in `protocol.json`. Instruction and data words are aligned address/value pairs. Integers may be decimal values or hexadecimal strings. Do not submit assembly, Python, encoder functions, or requests for controller-written code. Events refer to the active portion of the current action; reset uses part of its configured cycle budget.

The controller assigns the target and decides when to advance. Incidental hits are retained. State continues within a target and is reset when the controller changes targets. Invalid replies consume an attempt under the same protocol.

Read actual sampling expressions, gates, enumerations, and historical state from `coverage.sv.txt`. The coverage source is newer than the DUT snapshot: its PMP access-check results are mapped to the corresponding DUT request-error channels by read-only observation. This adaptation does not change DUT behavior.

Only the supplied public materials and current run's feedback are model inputs. Keep the conversation history continuous. Execution details and provider selection belong to the controller.