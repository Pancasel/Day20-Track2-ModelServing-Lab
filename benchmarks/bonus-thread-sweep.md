# Bonus — Thread sweep

Model: `qwen2.5-1.5b-instruct-q4_k_m.gguf`  ·  GPU layers: `99`

| threads | tg128 (tok/s) |
|---:|---:|
| 1 | 5.5 |
| 2 | 20.2 |
| 4 | 31.8 |
| 8 | 37.6 |
| 12 | 32.4 |
| 24 | 28.0 |

**Best**: `-t 8` at 37.6 tok/s.

Look at the curve. If it peaks around your **physical** core count and drops as you go higher, that's the memory-bandwidth ceiling: extra threads fight over the same memory channels and slow each other down.
