# Meeting archive method

Paper 2 includes every record marked `Completed` in the retained longitudinal KPI-related meeting log: **60 meetings** from 4 February 2025 through 24 March 2026.

## Recorded fields used

- Meeting number
- Date
- Day
- Start Time KSA
- End Time KSA
- Duration Minutes
- Phase
- Timezone
- Status

The meetings are recorded in Asia/Riyadh (UTC+3). Recorded duration is recomputed as end time minus start time and checked against `Duration Minutes`. The supplied log does not identify whether its start/end timestamps record actual meeting attendance or scheduled calendar slots. The reported quantity is the recorded time interval.

## Phase assignment

Paper 2 uses the archived phase field directly. No meeting is reassigned during analysis. The labels partly describe the recorded duration ranges. The supplied log contains no independent operational criterion explaining the original phase boundaries. The four blocks are used descriptively.

| Phase | Meetings | Dates | N | Recorded duration range (min) |
|---|---:|---|---:|---:|
| Phase 1 - Baseline | 1-11 | 2025-02-04 to 2025-04-15 | 11 | 60 |
| Phase 2 - Reduced 45-50m | 12-16 | 2025-04-22 to 2025-05-20 | 5 | 45-50 |
| Phase 3 - Variable 30-50m | 17-43 | 2025-05-27 to 2025-11-25 | 27 | 30-50 |
| Phase 4 - Short Focus 30-40m | 44-60 | 2025-12-02 to 2026-03-24 | 17 | 30-40 |

The full row-level log is `meeting_duration_log.csv`.
