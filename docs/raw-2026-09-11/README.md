# 2026-09-11 morning: the three big GLM-5.3-Flash files, Mac-heavy split (MacBook M5 Max 128 GB + Bosgame M5)

Setup: Mac client llama-bench (Metal, PR 27754 build d94f44e79) with the M5 as one RPC device (Vulkan, 27754
rpc-server rebuilt with `GGML_RPC_RDMA=OFF`, no `-c` file cache) over the Thunderbolt link 10.55.0.2:50052.
`-ts` order is RPC0/MTL0, i.e. the M5 share comes first. Size guard: M5 share <= 110 GB (`glm-row.sh`, `guarded-pass.sh`).

| file | -ts M5/Mac | M5 GB | Mac GB | pp512 t/s | tg128 t/s | note |
|---|---|---|---|---|---|---|
| Q3_K_XL 148 GB | 45/55 | 66 | 81 | 183.89 ± 6.83 | 13.78 ± 0.14 | the row in the table |
| Q3_K_XL 148 GB | 67/33 | 94 | 47 | 140.91 ± 3.00 | 11.35 ± 0.06 | M5-heavy by mistake (ts order), kept as a data point |
| Q3_K_XL 148 GB | 33/67 | 44 | 92 | 20.42 ± 6.08 | none | VOID: Mac GPU "Insufficient Memory", tg never ran |
| IQ4_XS 157 GB | 37/63 | 53 | 92 | 197.31 ± 4.46 | 15.23 ± 0.09 | the row in the table |
| Q4_K_XL 200 GB | any | >110 or Mac >90 | | | | does not fit this pair: 110 GB M5 ceiling and ~90 GB Mac Metal ceiling (`iogpu.wired_limit_mb` at default) |

Raw llama-bench output and the load logs' buffer lines are in the `.log` files here; scripts alongside.
