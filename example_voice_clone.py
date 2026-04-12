"""Exemplo de clone de voz com Qwen3-TTS 0.6B Base.

Requisitos:
- Áudio de referência: 5-10 segundos de voz limpa
- Transcrição do áudio de referência (use Whisper para transcrever)
- Modelo: Qwen/Qwen3-TTS-12Hz-0.6B-Base

Uso:
    python example_voice_clone.py
"""
import base64
import os
import subprocess
import tempfile

import soundfile as sf
import torch
from qwen_tts import Qwen3TTSModel

# --- CONFIGURAÇÃO ---
REF_AUDIO = "minha_voz.wav"       # seu áudio de referência (5-60s)
REF_TEXT = "Texto exato do que você falou no áudio de referência."  # transcrição
OUTPUT_FILE = "output_clone.mp3"

# Texto a ser gerado com sua voz
TEXT = "Olá! Essa é minha voz clonada pelo Qwen3-TTS rodando localmente."
LANGUAGE = "Portuguese"
INSTRUCT = "empolgado"  # opcional: tom da fala


def transcrever_audio(audio_path: str) -> str:
    """Usa Whisper medium para transcrever o áudio de referência."""
    import whisper
    print("Transcrevendo áudio com Whisper medium...")
    model = whisper.load_model("medium", device="cuda")
    result = model.transcribe(audio_path, language="pt")
    print(f"Transcrição: {result['text']}")
    return result["text"]


def gerar_clone(text: str, ref_audio: str, ref_text: str, instruct: str = "") -> str:
    """Gera áudio clonado e salva como MP3."""
    print(f"Carregando modelo Qwen3-TTS 0.6B Base...")
    model = Qwen3TTSModel.from_pretrained(
        "Qwen/Qwen3-TTS-12Hz-0.6B-Base",
        device_map="cuda:0",
        dtype=torch.bfloat16,
    )

    # Usa apenas os primeiros 10s do áudio de referência
    ref_tmp = "/tmp/ref_clip.wav"
    subprocess.run(
        ["ffmpeg", "-i", ref_audio, "-t", "10", "-ar", "16000", "-ac", "1", ref_tmp, "-y"],
        check=True, capture_output=True,
    )

    print("Gerando áudio clonado...")
    wavs, sr = model.generate_voice_clone(
        text=text,
        language=LANGUAGE,
        ref_audio=ref_tmp,
        ref_text=ref_text,
        instruct=instruct or None,
    )

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        sf.write(f.name, wavs[0], sr)
        wav_path = f.name

    mp3_path = OUTPUT_FILE
    subprocess.run(
        ["ffmpeg", "-i", wav_path, "-codec:a", "libmp3lame", "-qscale:a", "2", mp3_path, "-y"],
        check=True, capture_output=True,
    )
    os.unlink(wav_path)
    print(f"Áudio salvo em: {mp3_path}")
    return mp3_path


if __name__ == "__main__":
    # Se não tiver a transcrição, gera automaticamente com Whisper
    ref_text = REF_TEXT
    if not ref_text or ref_text == "Texto exato do que você falou no áudio de referência.":
        ref_text = transcrever_audio(REF_AUDIO)

    gerar_clone(TEXT, REF_AUDIO, ref_text, INSTRUCT)
