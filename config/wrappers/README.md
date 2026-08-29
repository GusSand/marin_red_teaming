# Wrapper set for Stage 1, step 4 (locked 2026-08-29)

| id | file | description |
|---|---|---|
| W0 | `w0_raw.txt` | raw continuation: `{instruction}` only, no scaffold |
| W1 | `w1_scaffold.txt` | current base scaffold (`config/base_template_v2.txt`, byte-identical) |
| W2 | `w2_explicit.txt` | scaffold + explicit instruction line |
| W3 | `w3_fewshot_benign.txt` | scaffold + two **benign-only** demonstrations. Format-showing, never stance-showing: both demos are innocuous "write an article" tasks with ordinary factual content. |

All are passed to safety-eval as `--model_input_template_path_or_name` (must contain `{instruction}`).
