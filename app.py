"""
AI4Bharat Indic-Parler-TTS — Local Hindi Text-to-Speech Web Application
Powered by Parler-TTS and Gradio.
"""

import os
import re
import sys
import tempfile
import time
import numpy as np
import soundfile as sf
import torch
import gradio as gr
from transformers import AutoTokenizer

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

try:
    from parler_tts import ParlerTTSForConditionalGeneration
except ImportError:
    ParlerTTSForConditionalGeneration = None

# Base directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models", "indic-parler-tts")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Hardware Detection
if torch.cuda.is_available():
    DEVICE = "cuda:0"
    DEVICE_NAME = torch.cuda.get_device_name(0)
    TORCH_DTYPE = torch.float32
    HARDWARE_STATUS = f"🚀 **GPU Accelerated**: {DEVICE_NAME} (CUDA enabled)"
else:
    DEVICE = "cpu"
    DEVICE_NAME = "CPU"
    TORCH_DTYPE = torch.float32
    HARDWARE_STATUS = "⚠️ **Running on CPU**: Generation may be slow. GPU with CUDA is recommended for real-time synthesis."

# Default Speaker Configurations & Descriptions
SPEAKER_CONFIGS = {
    "Rohit": "Rohit speaks with an expressive, articulate tone at a steady pace with clean audio quality and natural Hindi pronunciation.",
    "Divya": "Divya speaks with a clear, calm, and soothing voice delivered with gentle intonation and studio clarity in Hindi.",
    "Aman": "Aman speaks in a vibrant, engaging, and professional voice with precise Hindi diction and clear projection.",
    "Rani": "Rani speaks with a smooth, warm, and melodious voice at a moderate tempo in pristine acoustic conditions."
}
DEFAULT_SPEAKER = "Rohit"

# Global model & tokenizer handles (Loaded once and reused)
model = None
tokenizer = None
description_tokenizer = None
sampling_rate = 44100
model_load_error = None


def load_tts_model():
    """
    Load Indic-Parler-TTS model and dual tokenizers once into memory.
    """
    global model, tokenizer, description_tokenizer, sampling_rate, model_load_error

    if model is not None:
        return True, "Model is ready."

    if ParlerTTSForConditionalGeneration is None:
        model_load_error = "parler_tts package is not installed."
        return False, model_load_error

    config_file = os.path.join(MODEL_DIR, "config.json")
    if not os.path.exists(config_file):
        model_load_error = (
            "Model weights not found locally in 'models/indic-parler-tts'.\n"
            "The repository 'ai4bharat/indic-parler-tts' is gated on Hugging Face.\n\n"
            "Steps to download:\n"
            "1. Visit: https://huggingface.co/ai4bharat/indic-parler-tts and accept agreement.\n"
            "2. In terminal run: .\\.venv\\Scripts\\python.exe -c \"from huggingface_hub import login; login()\"\n"
            "3. Run: .\\.venv\\Scripts\\python.exe download_model.py"
        )
        return False, model_load_error

    print(f"[*] Loading Indic-Parler-TTS from '{MODEL_DIR}' onto {DEVICE}...", flush=True)
    try:
        model = ParlerTTSForConditionalGeneration.from_pretrained(
            MODEL_DIR,
            torch_dtype=TORCH_DTYPE,
            low_cpu_mem_usage=True
        ).to(DEVICE)
        model.eval()

        # Transcript Tokenizer (Hindi Text)
        tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)

        # Description Tokenizer (from text_encoder or local cache)
        local_desc_tok_dir = os.path.join(MODEL_DIR, "description_tokenizer")
        desc_tok_name = getattr(model.config.text_encoder, "_name_or_path", "google/flan-t5-large")

        if os.path.exists(local_desc_tok_dir) and os.path.exists(os.path.join(local_desc_tok_dir, "tokenizer_config.json")):
            description_tokenizer = AutoTokenizer.from_pretrained(local_desc_tok_dir)
        else:
            description_tokenizer = AutoTokenizer.from_pretrained(desc_tok_name)
            try:
                description_tokenizer.save_pretrained(local_desc_tok_dir)
            except Exception:
                pass

        sampling_rate = getattr(model.config, "sampling_rate", 44100)
        print(f"[OK] Indic-Parler-TTS loaded successfully! Sampling rate: {sampling_rate} Hz", flush=True)
        return True, f"Model loaded on {DEVICE_NAME} ({sampling_rate} Hz)"

    except Exception as e:
        model_load_error = f"Error initializing model: {str(e)}"
        print(f"[ERROR] {model_load_error}", flush=True)
        return False, model_load_error


def split_hindi_sentences(text: str, max_chunk_len: int = 140) -> list[str]:
    """
    Split Hindi text at sentence boundaries (।, ?, !, ., newlines) within model limits.
    """
    text = text.strip()
    if not text:
        return []

    # Split using Hindi danda (।), punctuation marks, and newlines
    raw_sentences = re.split(r'([।\.\?!;\n]+)', text)
    sentences = []
    
    current_sentence = ""
    for part in raw_sentences:
        if not part:
            continue
        if re.match(r'^[।\.\?!;\n]+$', part):
            current_sentence += part
            if current_sentence.strip():
                sentences.append(current_sentence.strip())
            current_sentence = ""
        else:
            current_sentence += part
            
    if current_sentence.strip():
        sentences.append(current_sentence.strip())

    # Pack sentences into chunks that do not exceed max_chunk_len
    chunks = []
    current_chunk = ""
    for sent in sentences:
        if not current_chunk:
            current_chunk = sent
        elif len(current_chunk) + len(sent) + 1 <= max_chunk_len:
            current_chunk += " " + sent
        else:
            chunks.append(current_chunk)
            current_chunk = sent

    if current_chunk:
        chunks.append(current_chunk)

    # Fallback if long uninterrupted text without punctuation
    final_chunks = []
    for chunk in chunks:
        if len(chunk) > max_chunk_len:
            words = chunk.split()
            sub = ""
            for w in words:
                if not sub:
                    sub = w
                elif len(sub) + len(w) + 1 <= max_chunk_len:
                    sub += " " + w
                else:
                    final_chunks.append(sub)
                    sub = w
            if sub:
                final_chunks.append(sub)
        else:
            final_chunks.append(chunk)

    return final_chunks if final_chunks else [text]


def synthesize_speech(hindi_text: str, speaker_name: str, voice_description: str):
    """
    Generate speech from Hindi text using Indic-Parler-TTS.
    """
    global model, tokenizer, description_tokenizer, sampling_rate, model_load_error

    # 1. Validation
    if not hindi_text or not hindi_text.strip():
        return None, None, "⚠️ **Please enter Hindi text to generate speech.**"

    # 2. Check model load
    if model is None:
        ok, msg = load_tts_model()
        if not ok:
            return None, None, f"❌ **Model Not Ready**:\n\n```\n{msg}\n```"

    # 3. Description fallback
    desc = voice_description.strip() if voice_description and voice_description.strip() else SPEAKER_CONFIGS.get(speaker_name, SPEAKER_CONFIGS[DEFAULT_SPEAKER])

    # 4. Text Chunking
    chunks = split_hindi_sentences(hindi_text)
    print(f"[*] Processing {len(chunks)} text segment(s)...", flush=True)

    generated_segments = []
    total_start_time = time.time()

    try:
        # Tokenize Description (input_ids and attention_mask for text encoder)
        desc_inputs = description_tokenizer(desc, return_tensors="pt")
        input_ids = desc_inputs.input_ids.to(DEVICE)
        attention_mask = desc_inputs.attention_mask.to(DEVICE)

        for i, chunk in enumerate(chunks, 1):
            print(f"[*] Processing segment {i}/{len(chunks)} (len={len(chunk)} chars)...", flush=True)
            
            # Tokenize Hindi Transcript (prompt_input_ids and prompt_attention_mask)
            prompt_inputs = tokenizer(chunk, return_tensors="pt")
            prompt_input_ids = prompt_inputs.input_ids.to(DEVICE)
            prompt_attention_mask = prompt_inputs.attention_mask.to(DEVICE)

            # Generate with inference mode & dual attention masks
            with torch.inference_mode():
                generation = model.generate(
                    input_ids=input_ids,
                    attention_mask=attention_mask,
                    prompt_input_ids=prompt_input_ids,
                    prompt_attention_mask=prompt_attention_mask,
                    do_sample=True,
                    temperature=1.0,
                    min_length=10,
                )

            audio_seg = generation.cpu().numpy().squeeze()
            if audio_seg.ndim > 1:
                audio_seg = audio_seg[0]

            generated_segments.append(audio_seg)

            # Add short silence between sentences if multi-segment
            if i < len(chunks):
                silence_gap = np.zeros(int(0.12 * sampling_rate), dtype=np.float32)
                generated_segments.append(silence_gap)

        # 5. Concatenate all audio segments into a single WAV
        final_audio = np.concatenate(generated_segments, axis=0)
        
        # Normalize audio to prevent clipping
        max_val = np.max(np.abs(final_audio))
        if max_val > 1.0:
            final_audio = final_audio / max_val * 0.98

        # 6. Save WAV file to output directory
        timestamp = int(time.time())
        output_filename = f"indic_tts_{speaker_name.lower()}_{timestamp}.wav"
        output_path = os.path.join(OUTPUT_DIR, output_filename)
        sf.write(output_path, final_audio, sampling_rate, format='WAV')

        elapsed = time.time() - total_start_time
        duration = len(final_audio) / sampling_rate
        rtf = elapsed / duration if duration > 0 else 0

        status_msg = (
            f"✅ **Synthesis Complete!**\n\n"
            f"• **Speaker**: {speaker_name}\n"
            f"• **Audio Duration**: {duration:.2f}s\n"
            f"• **Generation Time**: {elapsed:.2f}s ({rtf:.2f}x RTF)\n"
            f"• **Device**: {DEVICE_NAME} ({DEVICE})\n"
            f"• **Sample Rate**: {sampling_rate} Hz\n"
            f"• **Segments Processed**: {len(chunks)}"
        )

        return (sampling_rate, final_audio), output_path, status_msg

    except torch.cuda.OutOfMemoryError:
        torch.cuda.empty_cache()
        return None, None, "❌ **CUDA Out of Memory**: Try a shorter sentence or lower memory footprint."
    except Exception as e:
        return None, None, f"❌ **Generation Error**: {str(e)}"


def update_speaker_description(speaker_name: str) -> str:
    """
    Update voice description field when a speaker is selected.
    """
    return SPEAKER_CONFIGS.get(speaker_name, SPEAKER_CONFIGS[DEFAULT_SPEAKER])


# Build Gradio Interface
def build_app():
    load_success, load_message = load_tts_model()

    custom_css = """
    .gradio-container {
        max-width: 980px !important;
        margin: auto;
        font-family: system-ui, -apple-system, sans-serif;
    }
    .header-box {
        text-align: center;
        padding: 24px 16px;
        background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #0f172a 100%);
        border-radius: 12px;
        color: #ffffff;
        margin-bottom: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .header-box h1 {
        color: #ffffff !important;
        font-size: 2rem;
        margin-bottom: 8px;
    }
    .header-box p {
        color: #cbd5e1;
        font-size: 0.95rem;
    }
    .status-badge {
        display: inline-block;
        padding: 8px 14px;
        border-radius: 8px;
        margin-top: 10px;
        font-size: 0.88rem;
    }
    .generate-btn {
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%) !important;
        color: white !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 12px 24px !important;
        cursor: pointer;
    }
    """

    with gr.Blocks(title="AI4Bharat Indic-Parler-TTS (Hindi)") as demo:
        with gr.Column():
            gr.HTML(f"""
            <div class="header-box">
                <h1>🎙️ AI4Bharat Indic-Parler-TTS</h1>
                <p>High-Fidelity Neural Text-to-Speech for Hindi with Custom Voice Descriptions</p>
                <div class="status-badge" style="background: rgba(255, 255, 255, 0.08);">
                    {HARDWARE_STATUS}
                </div>
            </div>
            """)

            if not load_success:
                gr.Markdown(f"""
> [!WARNING]
> **Model Notice**: {load_message}
                """)

            with gr.Row():
                with gr.Column(scale=5):
                    hindi_input = gr.Textbox(
                        label="Hindi Text (हिंदी टेक्स्ट)",
                        placeholder="यहाँ हिंदी में टेक्स्ट लिखें... जैसे: नमस्ते! आपका स्वागत है। आज हम हिंदी में बात करेंगे।",
                        value="नमस्ते! आपका स्वागत है। आज हम हिंदी में बात करेंगे।",
                        lines=4,
                        max_lines=10,
                        elem_id="hindi-text-input"
                    )

                    with gr.Row():
                        speaker_dropdown = gr.Dropdown(
                            label="Select Speaker (वक्ता चुनें)",
                            choices=["Rohit", "Divya", "Aman", "Rani"],
                            value=DEFAULT_SPEAKER,
                            interactive=True,
                            elem_id="speaker-selector"
                        )

                    voice_desc_input = gr.Textbox(
                        label="Voice Description & Tone (आवाज विवरण)",
                        value=SPEAKER_CONFIGS[DEFAULT_SPEAKER],
                        lines=2,
                        interactive=True,
                        info="You can customize speech rate, emotion, tone, and acoustic room qualities.",
                        elem_id="voice-desc-input"
                    )

                    generate_btn = gr.Button(
                        "⚡ Generate Speech (आवाज बनाएं)",
                        variant="primary",
                        size="lg",
                        elem_classes=["generate-btn"],
                        elem_id="btn-generate"
                    )

                    # Quick Test Examples
                    gr.Examples(
                        examples=[
                            ["नमस्ते! आपका स्वागत है। आज हम हिंदी में बात करेंगे।", "Rohit", SPEAKER_CONFIGS["Rohit"]],
                            ["आर्टिफिशियल इंटेलिजेंस और मशीन लर्निंग हमारे जीवन को बदल रहे हैं।", "Divya", SPEAKER_CONFIGS["Divya"]],
                            ["यह एक उच्च गुणवत्ता वाली टेक्स्ट-टू-स्पीच प्रणाली है।", "Aman", SPEAKER_CONFIGS["Aman"]],
                            ["भारत की भाषाएं और संस्कृतियां अत्यंत समृद्ध और विविधतापूर्ण हैं।", "Rani", SPEAKER_CONFIGS["Rani"]]
                        ],
                        inputs=[hindi_input, speaker_dropdown, voice_desc_input],
                        label="Sample Hindi Prompts (नमूना वाक्य)"
                    )

                with gr.Column(scale=4):
                    audio_player = gr.Audio(
                        label="Generated Audio Player (ऑडियो प्लेयर)",
                        type="numpy",
                        autoplay=True,
                        elem_id="audio-player"
                    )

                    download_file = gr.File(
                        label="Download WAV File (WAV डाउनलोड)",
                        elem_id="download-wav-file"
                    )

                    status_display = gr.Markdown(
                        value="*Ready to generate Hindi speech. Click 'Generate Speech' above.*",
                        elem_id="status-output"
                    )

        # Event Bindings
        speaker_dropdown.change(
            fn=update_speaker_description,
            inputs=[speaker_dropdown],
            outputs=[voice_desc_input]
        )

        generate_btn.click(
            fn=synthesize_speech,
            inputs=[hindi_input, speaker_dropdown, voice_desc_input],
            outputs=[audio_player, download_file, status_display]
        )

    return demo


if __name__ == "__main__":
    print("=" * 70, flush=True)
    print("Starting AI4Bharat Indic-Parler-TTS Application...", flush=True)
    print(f"Device: {DEVICE_NAME} ({DEVICE})", flush=True)
    print("Binding to: http://127.0.0.1:7860 (localhost only, public sharing disabled)", flush=True)
    print("=" * 70, flush=True)

    demo = build_app()
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        inbrowser=False
    )
