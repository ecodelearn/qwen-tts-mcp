# qwen-tts-mcp

MCP server local para geração de áudio com **Qwen3-TTS** e envio via **Evolution API** (WhatsApp).

## Features

- 🎙️ Voz feminina padrão: **Ono_Anna** (Qwen3-TTS 1.7B CustomVoice)
- 🎤 Clone de voz: **Qwen3-TTS 0.6B Base** com áudio de referência
- ⚡ Texto longo ultra-rápido: **Piper TTS** (PT-BR, CPU, ~1.5s para 29s de áudio)
- 📱 Envio direto para WhatsApp via Evolution API

## Tools MCP

| Tool | Descrição |
|------|-----------|
| `tts_send_whatsapp` | Gera áudio com Ono_Anna e envia para WhatsApp |
| `tts_clone_send_whatsapp` | Clona voz de referência e envia para WhatsApp |
| `tts_faber_send_whatsapp` | Gera áudio com Piper Faber PT-BR e envia para WhatsApp |

## Requisitos

- Python 3.12+
- CUDA (RTX 3060 recomendado)
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
wget "https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx"
wget "https://huggingface.co/rhasspy/piper-voices/resolve/main/pt/pt_BR/faber/medium/pt_BR-faber-medium.onnx.json"
mv pt_BR-faber-medium.* piper-models/
```

## Configuração

Crie um `.env` com as credenciais da Evolution API:
```env
EVOLUTION_API_URL=https://sua-api.com
EVOLUTION_API_KEY=sua-chave
EVOLUTION_INSTANCE=nome-instancia
```

Configure a variável de ambiente:
```bash
export EVO_ENV_FILE=/caminho/para/.env
```

## Uso como MCP no Kiro CLI

Adicione em `~/.kiro/settings/mcp.json`:
```json
{
  "qwen-tts": {
    "command": "/caminho/.venv/bin/python",
    "args": ["/caminho/mcp_server.py"],
    "env": {
      "EVO_ENV_FILE": "/caminho/.env"
    }
  }
}
```

## Vozes Disponíveis

**Femininas:** `Ono_Anna` (padrão), `Vivian`, `Serena`, `Sohee`  
**Masculinas:** `Ryan`, `Aiden`, `Uncle_Fu`, `Dylan`, `Eric`

## Benchmarks (RTX 3060)

| Chars | Geração | Áudio |
|-------|---------|-------|
| 40 | 7.2s | 3.4s |
| 93 | 11.5s | 6.9s |
| 180 | 20.7s | 11.8s |
| 357 | 45.1s | 25.6s |

**Batch 4 chunks:** 12.5s vs chunk único: 31s → **2.5x mais rápido**  
**Sweet spot:** 100-150 chars por chunk

**Piper TTS:** 1.6s para 29s de áudio (CPU, sem GPU)
