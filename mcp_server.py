"""MCP server para Qwen3-TTS + envio de áudio via Evolution API."""
import asyncio
import base64
import json
import os
import subprocess
import tempfile

import httpx
import soundfile as sf
import torch
from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

load_dotenv(os.environ.get("EVO_ENV_FILE", "/home/ecode/Documents/projetos/pi-evo-tool/.env"))

server = Server("qwen-tts-mcp")
_model_custom = None
_model_clone = None

REF_AUDIO = "/home/ecode/minha_voz.wav"
REF_TEXT = "O rato roeu a roupa do rei de Roma. O Calé é amigo da garotada. O Sandeco em cima ia aplicada. Eu sou o da..."


def get_model_custom():
    global _model_custom
    if _model_custom is None:
        from qwen_tts import Qwen3TTSModel
        _model_custom = Qwen3TTSModel.from_pretrained(
            "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice",
            device_map="cuda:0",
            dtype=torch.bfloat16,
        )
    return _model_custom


def get_model_clone():
    global _model_clone
    if _model_clone is None:
        from qwen_tts import Qwen3TTSModel
        _model_clone = Qwen3TTSModel.from_pretrained(
            "Qwen/Qwen3-TTS-12Hz-0.6B-Base",
            device_map="cuda:0",
            dtype=torch.bfloat16,
        )
    return _model_clone


def to_mp3(wav_array, sr: int) -> str:
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        sf.write(f.name, wav_array, sr)
        wav_path = f.name
    return to_mp3_from_wav(wav_path)


def to_mp3_from_wav(wav_path: str) -> str:
    mp3_path = wav_path.replace(".wav", ".mp3")
    subprocess.run(
        ["ffmpeg", "-i", wav_path, "-codec:a", "libmp3lame", "-qscale:a", "2", mp3_path, "-y"],
        check=True, capture_output=True,
    )
    os.unlink(wav_path)
    return mp3_path


def evo_client():
    base_url = os.environ["EVOLUTION_API_URL"].rstrip("/")
    api_key = os.environ["EVOLUTION_API_KEY"]
    instance = os.environ["EVOLUTION_INSTANCE"]
    client = httpx.Client(
        base_url=base_url,
        headers={"apikey": api_key, "Content-Type": "application/json"},
        timeout=120,
    )
    return client, instance


def send_audio(to: str, mp3_path: str) -> dict:
    with open(mp3_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    os.unlink(mp3_path)
    client, instance = evo_client()
    r = client.post(f"/message/sendMedia/{instance}", json={
        "number": to,
        "mediatype": "audio",
        "media": b64,
        "fileName": "audio.mp3",
        "mimetype": "audio/mp3",
    })
    r.raise_for_status()
    return r.json()


@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="tts_send_whatsapp",
            description="Gera áudio com voz feminina Ono_Anna (padrão) e envia para WhatsApp. Para voz masculina use speaker='Ryan'.",
            inputSchema={
                "type": "object",
                "required": ["text", "to"],
                "properties": {
                    "text": {"type": "string"},
                    "to": {"type": "string", "description": "Número ou JID do grupo"},
                    "speaker": {"type": "string", "default": "Ono_Anna", "description": "Feminino: Ono_Anna(padrão), Vivian, Serena, Sohee. Masculino: Ryan, Aiden, Uncle_Fu, Dylan, Eric"},
                    "language": {"type": "string", "default": "Portuguese"},
                    "instruct": {"type": "string", "default": ""},
                },
            },
        ),
        types.Tool(
            name="tts_clone_send_whatsapp",
            description="Clona a voz masculina do dono (Qwen 0.6B) e envia áudio para WhatsApp.",
            inputSchema={
                "type": "object",
                "required": ["text", "to"],
                "properties": {
                    "text": {"type": "string"},
                    "to": {"type": "string"},
                    "language": {"type": "string", "default": "Portuguese"},
                    "instruct": {"type": "string", "default": "empolgado"},
                },
            },
        ),
        types.Tool(
            name="tts_faber_send_whatsapp",
            description="Gera áudio com voz masculina Faber PT-BR (Piper TTS — ultra rápido, ideal para textos longos) e envia para WhatsApp.",
            inputSchema={
                "type": "object",
                "required": ["text", "to"],
                "properties": {
                    "text": {"type": "string"},
                    "to": {"type": "string"},
                },
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    loop = asyncio.get_event_loop()

    if name == "tts_generate":
        def run():
            model = get_model_custom()
            wavs, sr = model.generate_custom_voice(
                text=arguments["text"],
                language=arguments.get("language", "Portuguese"),
                speaker=arguments.get("speaker", "Ono_Anna"),
                instruct=arguments.get("instruct") or None,
            )
            mp3 = to_mp3(wavs[0], sr)
            with open(mp3, "rb") as f:
                b64 = base64.b64encode(f.read()).decode()
            os.unlink(mp3)
            return b64
        b64 = await loop.run_in_executor(None, run)
        return [types.TextContent(type="text", text=json.dumps({"audio_base64": b64}))]

    elif name == "tts_send_whatsapp":
        def run():
            model = get_model_custom()
            wavs, sr = model.generate_custom_voice(
                text=arguments["text"],
                language=arguments.get("language", "Portuguese"),
                speaker=arguments.get("speaker", "Ono_Anna"),
                instruct=arguments.get("instruct") or None,
            )
            mp3 = to_mp3(wavs[0], sr)
            return send_audio(arguments["to"], mp3)
        result = await loop.run_in_executor(None, run)
        return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

    elif name == "tts_clone_send_whatsapp":
        def run():
            model = get_model_clone()
            wavs, sr = model.generate_voice_clone(
                text=arguments["text"],
                language=arguments.get("language", "Portuguese"),
                ref_audio=REF_AUDIO,
                ref_text=REF_TEXT,
                instruct=arguments.get("instruct", "empolgado"),
            )
            mp3 = to_mp3(wavs[0], sr)
            return send_audio(arguments["to"], mp3)
        result = await loop.run_in_executor(None, run)
        return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

    elif name == "tts_faber_send_whatsapp":
        def run():
            import numpy as np
            from piper import PiperVoice
            voice = PiperVoice.load(
                os.path.join(os.path.dirname(__file__), "piper-models/pt_BR-faber-medium.onnx")
            )
            chunks = list(voice.synthesize(arguments["text"]))
            audio = np.concatenate([c.audio_float_array for c in chunks])
            import soundfile as sf_mod
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                sf_mod.write(f.name, audio, chunks[0].sample_rate)
                wav_path = f.name
            mp3 = to_mp3_from_wav(wav_path)
            return send_audio(arguments["to"], mp3)
        result = await loop.run_in_executor(None, run)
        return [types.TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

    raise ValueError(f"Tool desconhecida: {name}")


def main():
    async def run():
        async with stdio_server() as (r, w):
            await server.run(r, w, server.create_initialization_options())
    asyncio.run(run())


if __name__ == "__main__":
    main()
