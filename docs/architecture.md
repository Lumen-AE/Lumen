# Modules

| Module | Responsibility |
|---|---|
| `engine` | Execution interfaces, scheduling, and feedback |
| `coverage` | Coverage definitions, scoring, and recount |
| `design` | Design knowledge and RTL graphs |
| `reasoning` | Coverage-goal binding and temporal decomposition |
| `observation` | Probe selection and evidence comparison |
| `memory` | Experience storage and prefix replay |
| `providers` | Model services and stimulus transport |
| `commands` | Command-line entry points |

DUT sources and hardware adapters are located in `targets/`. Configuration is in `profiles/`. The API and desktop relay use the same simulation client.
