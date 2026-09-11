# GLM-5.3-Flash 321B on two M5s, the corrected picture: raw log, 10 Sep 2026

The 31 Aug Reddit table redone after the Bosgame M5's memory fix (1 GB VRAM carve, 120 GB GTT, direct-IO loading).
Both ends on upstream PR 27754 (`d94f44e79`, on master `434ddbb`), MacBook = client (Metal), M5 = RPC device (Vulkan) over one Thunderbolt cable.
Card protocol: llama-bench pp512 / tg128, 3 runs; one coherence sample per row (llama-completion, "Explain in three sentences why the sky is blue.", temperature 0, 64 tokens).
The M5-solo column was measured by claudemm on the same commit (direct IO, balanced power profile).

## Why there are two sets of split rows

The first pass used the 3 Sep head of PR 27752 (`1d0c76f3c`). Its Vulkan backend has no kernels for the fused
hyper-connection ops (`GGML_OP_DSV4_HC_PRE/COMB/POST`, reused by glm5next). Alone, the M5 probes its device, sees
"not supported" and builds the unfused graph, so its text is sane. Behind RPC the client asks the RPC device whether
it supports the op, and `ggml_backend_rpc_device_supports_op` answers `true` for everything (a TODO in ggml-rpc.cpp),
so the fused ops were shipped to the M5 and computed as garbage: every split row measured a plausible speed and
printed punctuation soup. Isolations (all IQ2_XXS, same prompt): loopback Metal RPC device sane; M5 CPU device over
RPC sane; M5 Vulkan alone sane; M5 Vulkan behind RPC soup; with `LLAMA_FUSED_HC_DISABLE=1` on the client sane but
at the unfused speed (the Mac alone drops from 31.7 to 11.2 tokens/s the same way). PR 27754 sits on a master that
carries the Vulkan HC kernels (#26578), and on it the split is correct at full speed with nothing disabled.

## Rows (scratchpad glm-rows.md, verbatim)


## GLM-5.3-Flash IQ2_XXS-102GB, solo  (05:18:30Z)
### MacBook solo, Metal ngl 99 (3 runs)
| model                          |       size |     params | backend    | threads |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | ------: | --------------: | -------------------: |
| glm5next 312B.A17B IQ2_XXS - 2.0625 bpw |  94.84 GiB |   320.76 B | MTL,BLAS   |       6 |           pp512 |        509.30 ± 1.92 |
| glm5next 312B.A17B IQ2_XXS - 2.0625 bpw |  94.84 GiB |   320.76 B | MTL,BLAS   |       6 |           tg128 |         32.61 ± 0.62 |
coherence:  Explain in three sentences why the sky is blue. The sky appears blue because of a phenomenon called Rayleigh scattering, where sunlight interacts with molecules in Earth's atmosphere. Shorter wavelengths of light, like blue and violet, are scattered much more strongly than longer wavelengths like red and orange. Since our eyes are more sensitive to blue than violet, and some violet is absorbed hi
GLM-ROW-DONE IQ2_XXS-102GB solo 05:19:27Z

## GLM-5.3-Flash IQ1_S-93GB, solo  (05:48:27Z)
### MacBook solo, Metal ngl 99 (3 runs)
| model                          |       size |     params | backend    | threads |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | ------: | --------------: | -------------------: |
| glm5next 312B.A17B IQ1_S - 1.5625 bpw |  86.69 GiB |   320.76 B | MTL,BLAS   |       6 |           pp512 |        516.08 ± 2.57 |
| glm5next 312B.A17B IQ1_S - 1.5625 bpw |  86.69 GiB |   320.76 B | MTL,BLAS   |       6 |           tg128 |         34.10 ± 0.23 |
coherence:  Explain in three sentences why the sky is blue. The user is asking for an explanation of why the sky is blue, and they want it in exactly three sentences. I need to make sure I cover the key scientific concept—Rayleigh scattering—while keeping it concise and structured as three clear sentences.  Let me think about the science first. The sky is blue because of  
GLM-ROW-DONE IQ1_S-93GB solo 05:49:10Z

## GLM-5.3-Flash IQ2_XXS-102GB, split  (06:05:58Z)
M5 rpc-server (Vulkan) listening
### split, MacBook client (Metal) + M5 RPC device (Vulkan, 120 GB GTT), default tensor split (3 runs)
| model                          |       size |     params | backend    | threads |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | ------: | --------------: | -------------------: |
| glm5next 312B.A17B IQ2_XXS - 2.0625 bpw |  94.84 GiB |   320.76 B | MTL,BLAS,RPC |       6 |           pp512 |        319.10 ± 5.89 |
| glm5next 312B.A17B IQ2_XXS - 2.0625 bpw |  94.84 GiB |   320.76 B | MTL,BLAS,RPC |       6 |           tg128 |         17.37 ± 0.34 |
coherence:  Explain in three sentences why the sky is blue.  itylil,,.tll, ,(f: :   (vï. ooll freakllll .org.org.orgñancebe.org raf(e "   (n(e)(f(e(e(e(e(e(h(e(e(f(e(e(f(f(e(e(e(e(e.  
tensors cached on the M5: 163
window closed
llm-server active health=200; room agent active
GLM-ROW-DONE IQ2_XXS-102GB split 06:11:13Z

## GLM-5.3-Flash IQ4_XS-157GB, split  (06:11:13Z)
M5 rpc-server (Vulkan) listening
### split, MacBook client (Metal) + M5 RPC device (Vulkan, 120 GB GTT), default tensor split (3 runs)
| model                          |       size |     params | backend    | threads |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | ------: | --------------: | -------------------: |
| glm5next 312B.A17B IQ4_XS - 4.25 bpw | 146.04 GiB |   320.76 B | MTL,BLAS,RPC |       6 |           pp512 |        297.58 ± 1.00 |
| glm5next 312B.A17B IQ4_XS - 4.25 bpw | 146.04 GiB |   320.76 B | MTL,BLAS,RPC |       6 |           tg128 |         12.75 ± 0.12 |
coherence:  Explain in three sentences why the sky is blue. i,， ges, of of ofcerer oftgrtestgrgrterterrebcergrgr          (e              (a        (e(e(e(e  (e        (e      (e(e.e.e..(e(e.e  
tensors cached on the M5: 157
window closed
llm-server active health=200; room agent active
GLM-ROW-DONE IQ4_XS-157GB split 06:22:15Z

## GLM-5.3-Flash IQ1_S-93GB, solo  (06:22:15Z)
### MacBook solo, Metal ngl 99 (3 runs)
| model                          |       size |     params | backend    | threads |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | ------: | --------------: | -------------------: |
| glm5next 312B.A17B IQ1_S - 1.5625 bpw |  86.69 GiB |   320.76 B | MTL,BLAS   |       6 |           pp512 |        512.77 ± 2.67 |
| glm5next 312B.A17B IQ1_S - 1.5625 bpw |  86.69 GiB |   320.76 B | MTL,BLAS   |       6 |           tg128 |         31.62 ± 0.89 |
coherence:  Explain in three sentences why the sky is blue. The user is asking for an explanation of why the sky is blue, and they want it in exactly three sentences. I need to make sure I cover the key scientific concept—Rayleigh scattering—while keeping it concise and structured as three clear sentences.  Let me think about the science first. The sky is blue because of  
GLM-ROW-DONE IQ1_S-93GB solo 06:32:27Z

## GLM-5.3-Flash IQ2_XXS-102GB-hcoff, split  (07:05:40Z)
client switch: LLAMA_FUSED_HC_DISABLE=1 (fused hyper-connection ops are wrong on Vulkan behind RPC, measured 10 Sep)
M5 rpc-server (Vulkan) listening
### split, MacBook client (Metal) + M5 RPC device (Vulkan, 120 GB GTT), default tensor split (3 runs)

## GLM-5.3-Flash IQ1_S-93GB, split  (07:06:22Z)
| model                          |       size |     params | backend    | threads |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | ------: | --------------: | -------------------: |
| glm5next 312B.A17B IQ2_XXS - 2.0625 bpw |  94.84 GiB |   320.76 B | MTL,BLAS,RPC |       6 |           pp512 |        138.57 ± 2.98 |
| glm5next 312B.A17B IQ2_XXS - 2.0625 bpw |  94.84 GiB |   320.76 B | MTL,BLAS,RPC |       6 |           tg128 |          9.44 ± 0.05 |
coherence:  Explain in three sentences why the sky is blue. The sky appears blue because molecules in the air, primarily nitrogen and oxygen, scatter sunlight in all directions. This scattering is more effective at shorter wavelengths, so blue light is scattered more than other colors. This scattered blue light reaches our eyes from all parts of the sky, making it appear blue. [end of text]   
tensors cached on the M5: 0
window closed
llm-server active health=200; room agent active
GLM-ROW-DONE IQ2_XXS-102GB-hcoff split 07:10:36Z

## GLM-5.3-Flash IQ4_XS-157GB-hcoff, split  (07:10:36Z)
client switch: LLAMA_FUSED_HC_DISABLE=1 (fused hyper-connection ops are wrong on Vulkan behind RPC, measured 10 Sep)
M5 rpc-server (Vulkan) listening
### split, MacBook client (Metal) + M5 RPC device (Vulkan, 120 GB GTT), default tensor split (3 runs)

## GLM-5.3-Flash IQ2_XXS-102GB-27754, solo  (07:13:36Z, build /Users/petrus/llama-glm5-27754/build/bin)
| model                          |       size |     params | backend    | threads |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | ------: | --------------: | -------------------: |
| glm5next 312B.A17B IQ4_XS - 4.25 bpw | 146.04 GiB |   320.76 B | MTL,BLAS,RPC |       6 |           pp512 |        128.09 ± 2.46 |
| glm5next 312B.A17B IQ4_XS - 4.25 bpw | 146.04 GiB |   320.76 B | MTL,BLAS,RPC |       6 |           tg128 |          8.10 ± 0.04 |
coherence:  Explain in three sentences why the sky is blue. The sky appears blue because sunlight is made up of all colors, and as it enters Earth's atmosphere, it collides with tiny gas molecules. Blue light has a shorter wavelength than other colors, so it gets scattered in all directions much more strongly—a phenomenon called Rayleigh scattering. This scattered blue light reaches our eyes from  
tensors cached on the M5: 0
window closed
llm-server active health=200; room agent active
GLM-ROW-DONE IQ4_XS-157GB-hcoff split 07:21:12Z
client switch: LLAMA_FUSED_HC_DISABLE=1 (fused hyper-connection ops are wrong on Vulkan behind RPC, measured 10 Sep)
M5 rpc-server (Vulkan) listening
### split, MacBook client (Metal) + M5 RPC device (Vulkan, 120 GB GTT), default tensor split (3 runs)
| model                          |       size |     params | backend    | threads |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | ------: | --------------: | -------------------: |
| glm5next 312B.A17B IQ1_S - 1.5625 bpw |  86.69 GiB |   320.76 B | MTL,BLAS,RPC |       6 |           pp512 |        141.79 ± 2.81 |
| glm5next 312B.A17B IQ1_S - 1.5625 bpw |  86.69 GiB |   320.76 B | MTL,BLAS,RPC |       6 |           tg128 |          8.62 ± 0.08 |
coherence:  Explain in three sentences why the sky is blue. The user is asking for an explanation of why the sky is blue in exactly three sentences. I need to provide a concise, accurate explanation.  Key scientific concept: Rayleigh scattering. Sunlight enters Earth's atmosphere, which contains gas molecules (mostly nitrogen and oxygen). Shorter wavelengths (blue, violet) are scattered more  
tensors cached on the M5: 28
window closed
llm-server active health=200; room agent active
GLM-ROW-DONE IQ1_S-93GB split 07:26:39Z

## GLM-5.3-Flash Q3_K_XL-148GB, split  (07:26:39Z, build /Users/petrus/llama-glm5/build/bin)
client switch: LLAMA_FUSED_HC_DISABLE=1 (fused hyper-connection ops are wrong on Vulkan behind RPC, measured 10 Sep)
M5 rpc-server (Vulkan) listening
### split, MacBook client (Metal) + M5 RPC device (Vulkan, 120 GB GTT), default tensor split (3 runs)
| model                          |       size |     params | backend    | threads |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | ------: | --------------: | -------------------: |
| glm5next 312B.A17B Q3_K - Medium | 137.39 GiB |   320.76 B | MTL,BLAS,RPC |       6 |           pp512 |         68.61 ± 0.42 |
| glm5next 312B.A17B Q3_K - Medium | 137.39 GiB |   320.76 B | MTL,BLAS,RPC |       6 |           tg128 |          8.00 ± 0.10 |
coherence:  Explain in three sentences why the sky is blue. The sky appears blue because sunlight is composed of all colors, and as it enters Earth's atmosphere, shorter blue wavelengths scatter more than longer wavelengths due to Rayleigh scattering. This scattering happens because gas molecules in the air are more effective at deflecting shorter wavelengths of light. Our eyes then perceive this scattered b
tensors cached on the M5: 42
window closed
llm-server active health=200; room agent active
GLM-ROW-DONE Q3_K_XL-148GB split 07:36:01Z
### MacBook solo, Metal ngl 99 (3 runs)
| model                          |       size |     params | backend    | threads |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | ------: | --------------: | -------------------: |
| glm5next 313B.A17B IQ2_XXS - 2.0625 bpw |  94.84 GiB |   320.76 B | MTL,BLAS   |       6 |           pp512 |        490.79 ± 2.13 |
| glm5next 313B.A17B IQ2_XXS - 2.0625 bpw |  94.84 GiB |   320.76 B | MTL,BLAS   |       6 |           tg128 |         31.68 ± 0.17 |
coherence:  Explain in three sentences why the sky is blue. The sky appears blue because of a phenomenon called Rayleigh scattering, where sunlight interacts with molecules in Earth's atmosphere. Shorter wavelengths of light, like blue and violet, are scattered much more strongly than longer wavelengths like red and orange. Since our eyes are more sensitive to blue than violet, and some violet is absorbed hi
GLM-ROW-DONE IQ2_XXS-102GB-27754 solo 07:37:07Z

## GLM-5.3-Flash IQ1_S-93GB-27754, solo  (07:37:07Z, build /Users/petrus/llama-glm5-27754/build/bin)
### MacBook solo, Metal ngl 99 (3 runs)
| model                          |       size |     params | backend    | threads |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | ------: | --------------: | -------------------: |
| glm5next 313B.A17B IQ1_S - 1.5625 bpw |  86.69 GiB |   320.76 B | MTL,BLAS   |       6 |           pp512 |        491.31 ± 1.88 |
| glm5next 313B.A17B IQ1_S - 1.5625 bpw |  86.69 GiB |   320.76 B | MTL,BLAS   |       6 |           tg128 |         30.60 ± 0.62 |
coherence:  Explain in three sentences why the sky is blue. The user is asking for an explanation of why the sky is blue, and they want it in exactly three sentences. I need to make sure I cover the key scientific concept—Rayleigh scattering—while keeping it concise and structured as three clear sentences.  Let me think about the science first. The sky is blue because of  
GLM-ROW-DONE IQ1_S-93GB-27754 solo 07:37:57Z

## GLM-5.3-Flash Q4_K_XL-200GB, split  (07:38:01Z, build /Users/petrus/llama-glm5/build/bin)
client switch: LLAMA_FUSED_HC_DISABLE=1 (fused hyper-connection ops are wrong on Vulkan behind RPC, measured 10 Sep)
M5 rpc-server (Vulkan) listening
### split, MacBook client (Metal) + M5 RPC device (Vulkan, 120 GB GTT), default tensor split (3 runs)

## GLM-5.3-Flash IQ2_XXS-102GB-27754, split  (07:39:57Z, build /Users/petrus/llama-glm5-27754/build/bin)
| model                          |       size |     params | backend    | threads |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | ------: | --------------: | -------------------: |
| glm5next 312B.A17B Q4_K - Medium | 185.98 GiB |   320.76 B | MTL,BLAS,RPC |       6 |           pp512 |        129.34 ± 3.44 |
| glm5next 312B.A17B Q4_K - Medium | 185.98 GiB |   320.76 B | MTL,BLAS,RPC |       6 |           tg128 |          6.89 ± 0.02 |
coherence:  Explain in three sentences why the sky is blue. The sky appears blue because sunlight is composed of all colors, and as it enters Earth's atmosphere, it collides with gas molecules. Blue light has a shorter wavelength than other colors, causing it to scatter more strongly in all directions—a phenomenon known as Rayleigh scattering. This scattered blue light reaches our eyes from every part  
tensors cached on the M5: 64
window closed
llm-server active health=200; room agent active
GLM-ROW-DONE Q4_K_XL-200GB split 07:55:18Z
build /Users/petrus/llama-glm5-27754/build/bin, fused ops as shipped
M5 rpc-server (Vulkan) listening
### split, MacBook client (Metal) + M5 RPC device (Vulkan, 120 GB GTT), default tensor split (3 runs)
| model                          |       size |     params | backend    | threads |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | ------: | --------------: | -------------------: |
| glm5next 313B.A17B IQ2_XXS - 2.0625 bpw |  94.84 GiB |   320.76 B | MTL,BLAS,RPC |       6 |           pp512 |        186.40 ± 7.89 |
| glm5next 313B.A17B IQ2_XXS - 2.0625 bpw |  94.84 GiB |   320.76 B | MTL,BLAS,RPC |       6 |           tg128 |         16.78 ± 0.25 |
coherence:  Explain in three sentences why the sky is blue. The sky appears blue because molecules in the air scatter sunlight, and this scattering is much stronger for shorter wavelengths like blue than for longer ones like red. This phenomenon is called Rayleigh scattering. Since blue light is scattered in all directions across the sky, we see blue when we look up. [end of text]   
tensors cached on the M5: 0
window closed
llm-server active health=200; room agent active
GLM-ROW-DONE IQ2_XXS-102GB-27754 split 08:00:32Z

## GLM-5.3-Flash IQ1_S-93GB-27754, split  (08:00:32Z, build /Users/petrus/llama-glm5-27754/build/bin)
build /Users/petrus/llama-glm5-27754/build/bin, fused ops as shipped
M5 rpc-server (Vulkan) listening
### split, MacBook client (Metal) + M5 RPC device (Vulkan, 120 GB GTT), default tensor split (3 runs)
| model                          |       size |     params | backend    | threads |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | ------: | --------------: | -------------------: |
| glm5next 313B.A17B IQ1_S - 1.5625 bpw |  86.69 GiB |   320.76 B | MTL,BLAS,RPC |       6 |           pp512 |        187.69 ± 9.55 |
| glm5next 313B.A17B IQ1_S - 1.5625 bpw |  86.69 GiB |   320.76 B | MTL,BLAS,RPC |       6 |           tg128 |         17.12 ± 0.24 |
coherence:  Explain in three sentences why the sky is blue. The user is asking for an explanation of why the sky is blue in exactly three sentences. I need to provide a concise, accurate explanation.  Key scientific concept: Rayleigh scattering. Sunlight enters Earth's atmosphere, which contains gas molecules (mostly nitrogen and oxygen). These molecules scatter light, and shorter wavelengths (blue,  
tensors cached on the M5: 0
window closed
llm-server active health=200; room agent active
GLM-ROW-DONE IQ1_S-93GB-27754 split 08:05:47Z

## GLM-5.3-Flash Q3_K_XL-148GB-27754, split  (08:05:47Z, build /Users/petrus/llama-glm5-27754/build/bin)
build /Users/petrus/llama-glm5-27754/build/bin, fused ops as shipped
M5 rpc-server (Vulkan) listening
### split, MacBook client (Metal) + M5 RPC device (Vulkan, 120 GB GTT), default tensor split (3 runs)
| model                          |       size |     params | backend    | threads |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | ------: | --------------: | -------------------: |
| glm5next 313B.A17B Q3_K - Medium | 137.39 GiB |   320.76 B | MTL,BLAS,RPC |       6 |           pp512 |        172.13 ± 6.53 |
| glm5next 313B.A17B Q3_K - Medium | 137.39 GiB |   320.76 B | MTL,BLAS,RPC |       6 |           tg128 |         12.92 ± 0.34 |
coherence:  Explain in three sentences why the sky is blue. The sky appears blue because sunlight is composed of all colors, and as it enters Earth's atmosphere, shorter blue wavelengths scatter more than longer wavelengths due to Rayleigh scattering. This scattering happens because gas molecules in the air are more effective at deflecting shorter wavelengths of light. As a result, blue light is dispersed ac
tensors cached on the M5: 0
window closed
llm-server active health=200; room agent active
GLM-ROW-DONE Q3_K_XL-148GB-27754 split 08:14:20Z

## GLM-5.3-Flash IQ4_XS-157GB-27754, split  (08:14:20Z, build /Users/petrus/llama-glm5-27754/build/bin)
build /Users/petrus/llama-glm5-27754/build/bin, fused ops as shipped
M5 rpc-server (Vulkan) listening
### split, MacBook client (Metal) + M5 RPC device (Vulkan, 120 GB GTT), default tensor split (3 runs)
| model                          |       size |     params | backend    | threads |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | ------: | --------------: | -------------------: |
| glm5next 313B.A17B IQ4_XS - 4.25 bpw | 146.04 GiB |   320.76 B | MTL,BLAS,RPC |       6 |           pp512 |        166.08 ± 5.18 |
| glm5next 313B.A17B IQ4_XS - 4.25 bpw | 146.04 GiB |   320.76 B | MTL,BLAS,RPC |       6 |           tg128 |         12.38 ± 0.11 |
coherence:  Explain in three sentences why the sky is blue. The sky appears blue because sunlight is made up of all colors, and as it enters Earth's atmosphere, it collides with tiny gas molecules. Blue light has shorter, smaller waves than other colors, so it gets scattered in all directions much more strongly—a phenomenon called Rayleigh scattering. When we look up, we see  
tensors cached on the M5: 0
window closed
llm-server active health=200; room agent active
GLM-ROW-DONE IQ4_XS-157GB-27754 split 08:23:45Z

## GLM-5.3-Flash Q4_K_XL-200GB-27754, split  (08:23:45Z, build /Users/petrus/llama-glm5-27754/build/bin)
build /Users/petrus/llama-glm5-27754/build/bin, fused ops as shipped
M5 rpc-server (Vulkan) listening
### split, MacBook client (Metal) + M5 RPC device (Vulkan, 120 GB GTT), default tensor split (3 runs)
| model                          |       size |     params | backend    | threads |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | ------: | --------------: | -------------------: |
| glm5next 313B.A17B Q4_K - Medium | 185.98 GiB |   320.76 B | MTL,BLAS,RPC |       6 |           pp512 |        161.90 ± 4.46 |
| glm5next 313B.A17B Q4_K - Medium | 185.98 GiB |   320.76 B | MTL,BLAS,RPC |       6 |           tg128 |         11.91 ± 0.09 |
coherence:  Explain in three sentences why the sky is blue. The sky appears blue because sunlight is composed of all colors, and as it enters Earth's atmosphere, it collides with gas molecules. Blue light has a shorter wavelength than other colors, causing it to scatter more strongly in all directions—a phenomenon known as Rayleigh scattering. This scattered blue light reaches our eyes from every part  
tensors cached on the M5: 0
window closed
llm-server active health=200; room agent active
GLM-ROW-DONE Q4_K_XL-200GB-27754 split 08:35:07Z

## Isolations (scratchpad glm-diag.md, verbatim)


## GLM split garbage isolations 06:22:42Z, IQ2_XXS, temp 0, 64 tokens
T3 Mac client + loopback Metal RPC device:  Explain in three sentences why the sky is blue. The sky appears blue because of a phenomenon called Rayleigh scattering, where sunlight interacts with molecules in Earth's atmosphere. Shorter wavelengths of light, like blue and violet, are scattered much more strongly than longer wavelengths like r
T1 M5 alone, Vulkan 27752, llama-server:  Then explain in three sentences why the sky is not blue. Then explain in three sentences why the sky is blue. Then explain in three sentences why the sky is not blue. Then explain in three sentences why the sky is blue. Then explain in three sentences why the sky is not blue. Then explain in three 
M5 rpc-server (CPU) listening
T2 Mac client + M5 RPC device on CPU:  Explain in three sentences why the sky is blue. The sky appears blue because of a phenomenon called Rayleigh scattering. Sunlight contains all colors of light, but as it passes through the atmosphere, the shorter blue wavelengths are scattered more strongly by the gas molecules than longer waveleng
window closed
llm-server active health=200; room agent active
GLM-DIAG-DONE 06:31:08Z

## split with fused ops off on the client 06:44:15Z, IQ2_XXS, Mac client 27752 patched, M5 rpc-server 27752 Vulkan
M5 rpc-server (Vulkan) listening
F LLAMA_FUSED_GDN_DISABLE=1:  Explain in three sentences why the sky is blue. wood  7 _   P . . . . aNE wwwion http http http . __  y __ODODODODOD __woodford    $  r r  fictionson rsonsonsonson ${ED storage  __ron† storage . storage /**	 /** /** /** .  
0.53.979.974 W llama_context: fused-op switches: GDN disabled, HC on
F LLAMA_FUSED_HC_DISABLE=1:  Explain in three sentences why the sky is blue. The sky appears blue because molecules in the air, primarily nitrogen and oxygen, scatter sunlight in all directions. This scattering is more effective at shorter wavelengths, so blue light is scattered more than other colors. This scattered blue ligh
1.38.320.031 W llama_context: fused-op switches: GDN on, HC disabled
F LLAMA_FUSED_GDN_AUTO=1:  Explain in three sentences why the sky is blue.  itylil,,.tll, ,(f: :   (vï. ooll freakllll .org.org.orgñancebe.org raf(e "   (n(e)(f(e(e(e(e(e(h(e(e(f(e(e(f(f(e(e(e(e(e.  
1.15.788.709 W llama_context: fused-op switches: GDN auto-probed, HC on
window closed
llm-server active health=200; room agent active
GLM-FUSE-DONE 07:05:24Z

## Mac solo IQ2_XXS with LLAMA_FUSED_HC_DISABLE=1 (07:37:58Z)
| model                          |       size |     params | backend    | threads |            test |                  t/s |
| ------------------------------ | ---------: | ---------: | ---------- | ------: | --------------: | -------------------: |
| glm5next 312B.A17B IQ2_XXS - 2.0625 bpw |  94.84 GiB |   320.76 B | MTL,BLAS   |       6 |           pp512 |       204.12 ± 16.12 |
| glm5next 312B.A17B IQ2_XXS - 2.0625 bpw |  94.84 GiB |   320.76 B | MTL,BLAS   |       6 |           tg128 |         11.24 ± 0.39 |
SOLO-HCOFF-DONE 07:39:07Z
