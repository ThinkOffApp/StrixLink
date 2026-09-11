
## 27B Q4_K_XL, MacBook alone, Metal (card protocol 5 runs)  (23:23:10Z)
| model                          |       size |     params | backend    | threads |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | ------: | --------------: | -------------------: |
| qwen35 27B Q4_K - Medium       |  16.34 GiB |    27.32 B | MTL,BLAS   |       6 |           pp512 |        726.58 ± 2.57 |
| qwen35 27B Q4_K - Medium       |  16.34 GiB |    27.32 B | MTL,BLAS   |       6 |           tg128 |         25.45 ± 0.52 |

done 23:23:56Z

## 27B Q4_K_XL, M5 alone, Vulkan ngl 99 (new 1 GB carve + 120 GB GTT)  (23:23:56Z)
| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
| qwen35 27B Q4_K - Medium       |  16.34 GiB |    27.32 B | Vulkan     |  99 |           pp512 |       291.62 ± 28.60 |
| qwen35 27B Q4_K - Medium       |  16.34 GiB |    27.32 B | Vulkan     |  99 |           tg128 |         12.15 ± 0.02 |

done 23:25:57Z

## 27B Q4_K_XL, SPLIT MacBook (client, Metal) + M5 (rpc, Vulkan)  (23:25:57Z)
rpc-server listening on 10.55.0.2:50052
M5 vram 977 MiB, gtt 1040 MiB
| model                          |       size |     params | backend    | threads |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | ------: | --------------: | -------------------: |
| qwen35 27B Q4_K - Medium       |  16.34 GiB |    27.32 B | MTL,BLAS,RPC |       6 |           pp512 |        433.83 ± 4.88 |
| qwen35 27B Q4_K - Medium       |  16.34 GiB |    27.32 B | MTL,BLAS,RPC |       6 |           tg128 |         15.25 ± 0.13 |
M5 vram 979 MiB, gtt 1059 MiB
coherence: 
rpc-server stopped

done 23:26:47Z

## Nex Q4_K_M, SPLIT MacBook (client) + M5 (rpc)  vs Mac alone 3099/117  (23:26:47Z)
rpc-server listening on 10.55.0.2:50052
| model                          |       size |     params | backend    | threads |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | ------: | --------------: | -------------------: |
| qwen35moe 35B.A3B Q4_K - Medium |  19.70 GiB |    34.66 B | MTL,BLAS,RPC |       6 |           pp512 |       1431.88 ± 1.90 |
| qwen35moe 35B.A3B Q4_K - Medium |  19.70 GiB |    34.66 B | MTL,BLAS,RPC |       6 |           tg128 |         69.57 ± 2.76 |
M5 vram 984 MiB, gtt 1042 MiB
rpc-server stopped

done 23:27:22Z

## DeepSeek V4 Flash IQ3_XXS (4 shards), M5 alone, Vulkan ngl 99 (capacity test in 120 GB GTT)  (23:27:22Z)
Mem:             122           3          43           0          76         118
M5 vram 977 MiB, gtt 1077 MiB

done 23:43:37Z

## DeepSeek V4 Flash IQ3_XXS, SPLIT M5 (client, Vulkan) + MacBook (rpc, Metal)  (23:43:37Z)
rpc-server listening on 10.55.0.1:50052
| model                          |       size |     params | backend    | ngl |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | --------------: | -------------------: |
coherence (M5 client): 
MB rpc-server stopped

done 23:56:25Z

## DEEPSEEK WINDOW 2 00:00:56Z: Mac alone, split Mac-client, coherence samples
### DeepSeek IQ3_XXS, M5 alone, Vulkan ngl 99, direct-IO load (-lm dio, claudemm's fix for the page-cache double copy), 3 runs
Mem:             122           3          93           0          26         119

## DEEPSEEK WINDOW 2 00:11:27Z: Mac alone, split Mac-client, coherence samples
### DeepSeek IQ3_XXS, M5 alone, Vulkan ngl 99, direct-IO load (-lm dio, claudemm's fix for the page-cache double copy), 3 runs
Mem:             122           5          58           0          59         116
| model                          |       size |     params | backend    | ngl |         lm |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | ---------: | --------------: | -------------------: |
| deepseek4 ?B IQ3_XXS - 3.0625 bpw |  97.05 GiB |   284.33 B | Vulkan     |  99 |        dio |           pp512 |        140.30 ± 4.35 |
| deepseek4 ?B IQ3_XXS - 3.0625 bpw |  97.05 GiB |   284.33 B | Vulkan     |  99 |        dio |           tg128 |         18.56 ± 0.01 |
gtt after: 1077 MiB
coherence Strix alone (dio): 
### DeepSeek IQ3_XXS, MacBook alone, Metal ngl 99 (3 runs)
| model                          |       size |     params | backend    | threads |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | ------: | --------------: | -------------------: |
| deepseek4 ?B IQ3_XXS - 3.0625 bpw |  97.05 GiB |   284.33 B | MTL,BLAS   |       6 |           pp512 |        584.43 ± 2.29 |
| deepseek4 ?B IQ3_XXS - 3.0625 bpw |  97.05 GiB |   284.33 B | MTL,BLAS   |       6 |           tg128 |         32.40 ± 0.03 |
coherence Mac alone: Explain in three sentences why the sky is blue.The sky appears blue because of a phenomenon called Rayleigh scattering, where sunlight is scattered in all directions by the gases and particles in Earth's atmosphere. Blue light has a shorter wavelength and is scattered much more strongly than other colors, so we see it from every direction. This scattering effect makes the entire sky look blue during the  
### DeepSeek IQ3_XXS, SPLIT MacBook (client, Metal) + M5 (rpc, Vulkan)
rpc-server listening on the M5
| model                          |       size |     params | backend    | threads |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | ------: | --------------: | -------------------: |
coherence split Mac-client: 
rpc tensors cached on the M5 during this split: 0
### coherence, Strix alone and split Strix-client (llama-completion on the M5)
### DeepSeek IQ3_XXS, SPLIT M5 (client, Vulkan, -lm dio) + MacBook (rpc, Metal), rerun with full output captured

## DEEPSEEK WINDOW 2 00:37:55Z: Mac alone, split Mac-client, coherence samples
(Strix-alone row already recorded above, skipped)
bench rc and last lines:
ggml_vulkan: Found 1 Vulkan devices:
ggml_vulkan: 0 = Radeon 8060S Graphics (RADV STRIX_HALO) (radv) | uma: 1 | fp16: 1 | bf16: 0 | fp4: 0 | warp size: 64 | shared memory: 65536 | int dot: 1 | matrix cores: KHR_coopmat
coherence Strix alone (dio, c 4096): Explain in three sentences why the sky is blue.The sky appears blue because of a phenomenon called Rayleigh scattering, where sunlight is scattered in all directions by the gases and particles in Earth's atmosphere. Blue light has a shorter wavelength and is scattered much more strongly than other colors, so we see it coming from all parts of the sky. During sunrise or sunset, the light  
### DeepSeek IQ3_XXS, MacBook alone, Metal ngl 99 (3 runs)
| model                          |       size |     params | backend    | threads |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | ------: | --------------: | -------------------: |
| deepseek4 ?B IQ3_XXS - 3.0625 bpw |  97.05 GiB |   284.33 B | MTL,BLAS   |       6 |           pp512 |        584.45 ± 3.15 |
| deepseek4 ?B IQ3_XXS - 3.0625 bpw |  97.05 GiB |   284.33 B | MTL,BLAS   |       6 |           tg128 |         33.42 ± 0.00 |
coherence Mac alone: Explain in three sentences why the sky is blue.The sky appears blue because of a phenomenon called Rayleigh scattering, where sunlight is scattered in all directions by the gases and particles in Earth's atmosphere. Blue light has a shorter wavelength and is scattered much more strongly than other colors, so we see it from every direction. This scattering effect makes the entire sky look blue during the  
### DeepSeek IQ3_XXS, SPLIT MacBook (client, Metal) + M5 (rpc, Vulkan)
rpc-server listening on the M5
| model                          |       size |     params | backend    | threads |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | ------: | --------------: | -------------------: |
| deepseek4 ?B IQ3_XXS - 3.0625 bpw |  97.05 GiB |   284.33 B | MTL,BLAS,RPC |       6 |           pp512 |       235.02 ± 10.37 |
| deepseek4 ?B IQ3_XXS - 3.0625 bpw |  97.05 GiB |   284.33 B | MTL,BLAS,RPC |       6 |           tg128 |         20.24 ± 0.04 |
coherence split Mac-client: Explain in three sentences why the sky is blue.The sky appears blue because of a phenomenon called Rayleigh scattering, where sunlight is scattered in all directions by the gases and particles in Earth's atmosphere. Blue light has a shorter wavelength and is scattered much more strongly than other colors, so we see it from every direction. This scattering effect makes the entire sky look blue during the  
rpc tensors cached on the M5 during this split: 18
### coherence, Strix alone and split Strix-client (llama-completion on the M5)
### DeepSeek IQ3_XXS, SPLIT M5 (client, Vulkan, -lm dio) + MacBook (rpc, Metal), rerun with full output captured
| model                          |       size |     params | backend    | ngl |         lm |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | --: | ---------: | --------------: | -------------------: |
| deepseek4 ?B IQ3_XXS - 3.0625 bpw |  97.05 GiB |   284.33 B | Vulkan,RPC |  99 |        dio |           pp512 |       234.29 ± 12.55 |
| deepseek4 ?B IQ3_XXS - 3.0625 bpw |  97.05 GiB |   284.33 B | Vulkan,RPC |  99 |        dio |           tg128 |         19.30 ± 0.08 |
bench rc and last lines:
| deepseek4 ?B IQ3_XXS - 3.0625 bpw |  97.05 GiB |   284.33 B | Vulkan,RPC |  99 |        dio |           pp512 |       234.29 ± 12.55 |
| deepseek4 ?B IQ3_XXS - 3.0625 bpw |  97.05 GiB |   284.33 B | Vulkan,RPC |  99 |        dio |           tg128 |         19.30 ± 0.08 |

build: 434ddbb (345)
split Strix-client coherence: Explain in three sentences why the sky is blue.The sky appears blue because of a phenomenon called Rayleigh scattering, where sunlight is scattered in all directions by the gases and particles in Earth's atmosphere. Blue light has a shorter wavelength and is scattered much more strongly than other colors, so we see it from every direction. This scattering effect makes the entire sky look blue during the  
window closed
llm-server active health=200; room agent active
EXTRA-DONE 00:57:36Z

## DEEPSEEK ROW 7, MacBook (M5 Max, Metal): speculative decoding, PR 8 protocol, warm-up call before each set 00:57:54Z
### baseline
  code      pp    80.8 t/s  gen  32.55 t/s  n=256  acc=-  wall   8.3s
  summary   pp    91.9 t/s  gen  32.69 t/s  n=256  acc=-  wall   8.2s
  reasoning pp   143.4 t/s  gen  32.54 t/s  n=256  acc=-  wall   8.2s
  list      pp    83.1 t/s  gen  31.91 t/s  n=256  acc=-  wall   8.3s
  chat      pp    81.0 t/s  gen  31.48 t/s  n=256  acc=-  wall   8.5s
| MacBook DS IQ3_XXS baseline | pp 96.0 ± 24.0 | gen 32.23 ± 0.47 | acceptance n/a | 5 prompts x 256 tokens, temp 0 |
### drafted (--spec-type draft-dspark --spec-draft-n-max 3)
Traceback (most recent call last):
  File "/private/tmp/claude-501/-Users-petrus/45ce8ac1-39c5-4b4e-aa22-10c15a606b54/scratchpad/specbench/spec_bench.py", line 10, in <module>
    urllib.request.urlopen(urllib.request.Request(url.rstrip("/") + "/completion", data=json.dumps(warm).encode(), headers={"Content-Type": "application/json"}), timeout=1800).read()
    ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.3_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/urllib/request.py", line 187, in urlopen
    return opener.open(url, data, timeout)
           ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.3_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/urllib/request.py", line 493, in open
    response = meth(req, response)
  File "/opt/homebrew/Cellar/python@3.14/3.14.3_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/urllib/request.py", line 602, in http_response
    response = self.parent.error(
        'http', request, response, code, msg, hdrs)
  File "/opt/homebrew/Cellar/python@3.14/3.14.3_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/urllib/request.py", line 531, in error
    return self._call_chain(*args)
           ~~~~~~~~~~~~~~~~^^^^^^^
  File "/opt/homebrew/Cellar/python@3.14/3.14.3_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/urllib/request.py", line 464, in _call_chain
    result = func(*args)
  File "/opt/homebrew/Cellar/python@3.14/3.14.3_1/Frameworks/Python.framework/Versions/3.14/lib/python3.14/urllib/request.py", line 611, in http_error_default
    raise HTTPError(req.full_url, code, msg, hdrs, fp)
urllib.error.HTTPError: HTTP Error 500: Internal Server Error
server log tail: 0.08.652.554 I common_speculative_impl_draft_dflash: - n_max=3, n_min=0, p_min=0.00 0.08.652.554 I common_speculative_impl_draft_dflash: - block_size=5, mask_token_id=128799, n_extract=3, sample_from_anchor=true 
SPEC-MAC-DONE 00:59:17Z

## DEEPSEEK ROW 7, MacBook (M5 Max, Metal): speculative decoding, PR 8 protocol, warm-up call before each set 01:00:28Z
(baseline recorded above: gen 32.23 ± 0.47, pp 96.0 ± 24.0, -c 8192)

## DEEPSEEK ROW 7, MacBook (M5 Max, Metal): speculative decoding, PR 8 protocol, warm-up call before each set 01:13:14Z
(baseline recorded above: gen 32.23 ± 0.47, pp 96.0 ± 24.0, -c 8192)
### drafted (--spec-type draft-dspark --spec-draft-n-max 3)
  code      pp    90.4 t/s  gen  30.04 t/s  n=256  acc=53%  wall   8.9s
  summary   pp    89.1 t/s  gen  28.83 t/s  n=256  acc=50%  wall   9.2s
  reasoning pp   129.8 t/s  gen  37.03 t/s  n=256  acc=75%  wall   7.3s
  list      pp    80.5 t/s  gen  30.91 t/s  n=256  acc=58%  wall   8.6s
  chat      pp    79.7 t/s  gen  27.00 t/s  n=256  acc=48%  wall   9.8s
| MacBook DS IQ3_XXS + DSpark bf16/mxfp4 draft on 0 GPU layers (-ngld), spec-draft-n-max 3, c 4096 | pp 93.9 ± 18.4 | gen 30.76 ± 3.40 | acceptance 57% | 5 prompts x 256 tokens, temp 0 |
server log tail: 1.02.676.708 I slot print_timing: id  3 | task 330 | draft acceptance = 0.58065 (  162 accepted /   279 generated), mean len =  2.74 1.12.475.741 I slot print_timing: id  2 | task 426 | draft acceptance = 0.48397 (  151 accepted /   312 generated), mean len =  2.45 
SPEC-MAC-DONE 01:14:28Z
