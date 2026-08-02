# Model routing

Canonical model-routing rules for the herd.  
**Updated 2026-08-02:** non-working models pruned; **cerebras / mistral / groq providers removed** from all agents.

## Allowed providers only

| Priority | Provider | Default / primary model | Notes |
|----------|----------|-------------------------|-------|
| **0** | `or-free` | `nvidia/nemotron-3-super-120b-a12b:free` | Free OpenRouter; pi default |
| **1** | `or-free` | `inclusionai/ling-3.0-flash:free` | Fastest free tools |
| **2** | `nvidia` | `openai/gpt-oss-20b` | NIM (key rotated 2026-08-02) |
| **3** | `ollama-cloud` | `minimax-m3` | ollama.com |
| 4 | `or-free` | `openrouter/free` | Emergency auto-route |

**Forbidden providers (removed from configs):** `cerebras`, `mistral`, `groq`.  
Do not launch `pi-cerebras` / `pi-mistral` / `pi-groq`.

## OpenRouter free (14 in pi)

`nvidia/nemotron-3-super-120b-a12b:free`, `inclusionai/ling-3.0-flash:free`, `openai/gpt-oss-20b:free`, `nvidia/nemotron-3-ultra-550b-a55b:free`, `nvidia/nemotron-3-nano-30b-a3b:free`, `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free`, `poolside/laguna-s-2.1:free`, `poolside/laguna-xs-2.1:free`, `cohere/north-mini-code:free`, `google/gemma-4-26b-a4b-it:free`, `nvidia/nemotron-nano-12b-v2-vl:free`, `nvidia/nemotron-nano-9b-v2:free`, `openrouter/free`, `nvidia/nemotron-3.5-content-safety:free`

## Ollama Cloud (7)

`gemma4:31b`, `gpt-oss:120b`, `gpt-oss:20b`, `minimax-m3`, `nemotron-3-nano:30b`, `nemotron-3-super`, `nemotron-3-ultra`

## NVIDIA NIM (17)

`openai/gpt-oss-20b`, nemotron-3 super/ultra/nano/omni, nano-9b/12b-vl, llama-3.3-nemotron-super 49b, minimax-m3, glm-5.2, deepseek-v4 flash/pro, llama-3.3/3.1-70b, step-3.7-flash, `mistralai/mistral-nemotron` (**NIM model id**, not Mistral provider)

## Fallback chain

1. `or-free` / ling-3.0-flash:free  
2. `or-free` / nemotron-3-super free  
3. `nvidia` / gpt-oss-20b  
4. `ollama-cloud` / minimax-m3  
5. `or-free` / openrouter/free  

## Never use
- Providers: cerebras, mistral, groq  
- `tencent/hy3:free`, `google/gemma-4-31b-it:free`, NIM `openai/gpt-oss-120b`  

## Config paths
| Agent | File |
|-------|------|
| **pi** | `~/.pi/agent/models.json`, `settings.json` |
| **pi mirror** | `Sync/Configs/pi/` |
| **Hermes** | `%LOCALAPPDATA%/hermes/config.yaml`, `~/.hermes/config.yaml` |

## Launch
```powershell
pi -ne --provider or-free --model inclusionai/ling-3.0-flash:free --tools read,bash,edit,write,grep,find,ls
pi -ne --provider nvidia --model openai/gpt-oss-20b --tools read,bash,edit,write,grep,find,ls
pi -ne --provider ollama-cloud --model minimax-m3 --tools read,bash,edit,write,grep,find,ls
```
