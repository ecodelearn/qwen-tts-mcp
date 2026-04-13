# qwen-tts-mcp

MCP server local para geração de áudio com **Qwen3-TTS** e envio via **Evolution API** (WhatsApp).

## Features

- 👩 Voz feminina: **Ono_Anna** via Qwen3-TTS **1.7B-CustomVoice**
- 🎤 Voz masculina: **clone do dono** via Qwen3-TTS **0.6B-Base** + `minha_voz.wav`
- ⚡ Textos longos: **Piper TTS** PT-BR (CPU, ~1.5s para 29s de áudio)
- 📱 Envio direto para WhatsApp via Evolution API

## Modelos

| Modelo HuggingFace | Uso | VRAM |
|--------------------|-----|------|
| `Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice` | Speakers pré-definidos (Anna, Ryan…) | ~4GB |
| `Qwen/Qwen3-TTS-12Hz-0.6B-Base` | Clone de voz com áudio de referência | ~2GB |

Os modelos são baixados automaticamente pelo HuggingFace na primeira execução e ficam em `~/.cache/huggingface/hub/`.

## Tools MCP

| Tool | Modelo | Voz |
|------|--------|-----|
| `tts_send_whatsapp` | 1.7B-CustomVoice | Feminina **Ono_Anna** (padrão) — outros speakers via parâmetro |
| `tts_clone_send_whatsapp` | 0.6B-Base | **Clone do dono** via `minha_voz.wav` |
| `tts_faber_send_whatsapp` | Piper TTS | Masculina **Faber PT-BR** — ideal para textos longos |

## Requisitos

- Python 3.12+
- CUDA (testado RTX 3060 12GB)
- `ffmpeg` instalado no sistema
- Evolution API configurada

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate
pip install qwen-tts piper-tts soundfile httpx python-dotenv torch
```

Baixar modelo Piper PT-BR:
```bash
mkdir -p piper-models
wget -P piper-models "https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx"
wget -P piper-models "https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx.json"
```

## Configuração

### .env (Evolution API)

```env
EVOLUTION_API_URL=https://sua-api.com
EVOLUTION_API_KEY=sua-chave
EVOLUTION_INSTANCE=nome-instancia
```

```bash
export EVO_ENV_FILE=/caminho/para/.env
```

### Clone de voz (minha_voz.wav)

O `tts_clone_send_whatsapp` usa dois parâmetros fixos no topo do `mcp_server.py`:

```python
REF_AUDIO = "/home/ecode/minha_voz.wav"   # áudio de referência (5-60s, voz limpa)
REF_TEXT  = "transcrição exata do áudio"   # use Whisper para transcrever
```

Para gerar a transcrição com Whisper:
```python
import whisper
model = whisper.load_model("medium", device="cuda")
result = model.transcribe("minha_voz.wav", language="pt")
print(result["text"])
```

## Uso como MCP no Kiro CLI

`~/.kiro/settings/mcp.json`:
```json
{
  "qwen-tts": {
    "command": "/home/ecode/Documents/projetos/qwen-tts-mcp/.venv/bin/python",
    "args": ["/home/ecode/Documents/projetos/qwen-tts-mcp/mcp_server.py"],
    "env": {
      "EVO_ENV_FILE": "/home/ecode/Documents/projetos/pi-evo-tool/.env"
    }
  }
}
```

## Vozes Disponíveis (1.7B-CustomVoice)

**Femininas:** `Ono_Anna` (padrão), `Vivian`, `Serena`, `Sohee`  
**Masculinas:** `Ryan`, `Aiden`, `Uncle_Fu`, `Dylan`, `Eric`

## Benchmarks (RTX 3060 12GB)

| Chars | Geração | Áudio |
|-------|---------|-------|
| 40 | 7.2s | 3.4s |
| 93 | 11.5s | 6.9s |
| 180 | 20.7s | 11.8s |
| 357 | 45.1s | 25.6s |

**Piper TTS:** ~1.6s para 29s de áudio (CPU, sem GPU)
