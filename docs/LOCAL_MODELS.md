# Running CodeConCat with Local LLMs

CodeConCat now ships with a unified `LocalServerProvider` that speaks the OpenAI
chat-completions API. The new provider powers presets for vLLM, LM Studio, and
the llama.cpp HTTP server, while still supporting generic OpenAI-compatible
runtimes like TGI, LocalAI, and FastChat.

The quickest way to get started is the guided wizard:

```bash
codeconcat config local-llm
```

The wizard will detect a running server, auto-discover an available model, and
write the required fields to `.codeconcat.yml`.

---

## Supported Presets

| Preset | Default URL | Notes |
| --- | --- | --- |
| vLLM | `http://localhost:8000` | Fast server for large GGUF/transformer models |
| LM Studio | `http://localhost:1234` | Desktop UI with OpenAI-compatible REST bridge |
| llama.cpp server | `http://localhost:8080` | Lightweight server bundled with llama.cpp |
| Generic local server | `http://localhost:8000` | TGI, LocalAI, FastChat, Oobabooga, etc. |

All presets share the same behaviour:

- Health probes cover `/health`, `/healthz`, `/readyz`, `/status`, and `/v1/health`.
- Model discovery requests `/v1/models` and `/models` and picks the first entry
  when no model name is configured.
- Connection validation falls back to a single-token chat completion so servers
  that expose only `/chat/completions` still pass.

---

## Step-by-Step Setup

### 1. Start Your Server

1. **vLLM**
   ```bash
   python -m vllm.entrypoints.openai.api_server \
     --model path/to/model \
     --host 0.0.0.0 --port 8000
   ```
2. **LM Studio** – open the LM Studio desktop UI, choose a model, and click
   “Start Server (OpenAI Compatible)”.
3. **llama.cpp server**
   ```bash
   ./llama-server -m models/llama-2-7b-chat.gguf -c 4096 -ngl 35
   ```
4. **Generic runtime** – run the provider-specific command (TGI, LocalAI, etc.)
   pointing at a port that exposes the OpenAI REST shape.

### 2. Run the Wizard

```bash
codeconcat config local-llm
```

You will be prompted to:

1. Pick the preset (vLLM / LM Studio / llama.cpp server / Generic).
2. Provide an API key if your server enforces authentication (leave blank
   otherwise).
3. Confirm or edit the detected base URL.
4. Choose a model from the discovered list, or type a custom name.

### 3. Generate Summaries

```bash
codeconcat run --ai-summary
```

You can still override per-run settings with `--ai-provider`,
`--ai-api-base`, and `--ai-model`.

---

## Example `.codeconcat.yml`

```yaml
enable_ai_summary: true
ai_provider: vllm
ai_api_base: http://localhost:8000
ai_model: mistral-7b-instruct
ai_api_key: ""  # Optional, leave empty for unauthenticated servers
ai_temperature: 0.2
ai_max_tokens: 600
```

Any preset can be swapped simply by changing `ai_provider` and `ai_api_base`.

---

## Troubleshooting

- **"Connection refused"** – ensure the server is running and listening on the
  configured port. The wizard probes multiple health endpoints but cannot start
  the server for you.
- **401/403 during validation** – the server expects an API key. Re-run the
  wizard and supply the token (or set `LOCAL_LLM_API_KEY`, `VLLM_API_KEY`,
  `LMSTUDIO_API_KEY`, or `LLAMACPP_SERVER_API_KEY`).
- **"Unable to auto-discover a model"** – the server did not respond to
  `/v1/models` or `/models`. Run `codeconcat config local-llm` again and type the
  model name manually, or export `LOCAL_LLM_MODEL`.
- **Slow responses** – decrease `ai_temperature`, shorten prompts, or
  enable streaming in your server configuration. vLLM typically offers the
  lowest latency, followed by llama.cpp server and LM Studio.
- **Token mismatch warnings** – some runtimes omit usage metrics. CodeConCat
  will still display summaries but the `tokens_used` field may stay at 0.

---

## Performance Notes

Relative throughput from local testing on an M3 Max laptop (batch size 1):

| Runtime | Model | Avg. tokens/sec | Notes |
| --- | --- | --- | --- |
| vLLM | Mistral-7B-Instruct | ~60 | Best concurrency + streaming |
| llama.cpp server | Llama-3.1-8B Q4 | ~18 | Very memory efficient |
| LM Studio | Mixtral-8x7B | ~14 | Easiest UX; UI + REST in one |

Actual numbers depend on hardware, quantization, and context length, but vLLM
is generally fastest, while LM Studio prioritises ease-of-use.

For more examples see the README section on local models.
