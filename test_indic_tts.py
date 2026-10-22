"""
Test script for AI4Bharat Indic-Parler-TTS
Generates speech for the test sentence: 'नमस्ते! आपका स्वागत है। आज हम हिंदी में बात करेंगे।'
"""
import os
import sys
import time
import numpy as np
import soundfile as sf
import torch
from transformers import AutoTokenizer
from parler_tts import ParlerTTSForConditionalGeneration

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "models", "indic-parler-tts")
DESC_TOK_DIR = os.path.join(MODEL_DIR, "description_tokenizer")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)

DEVICE = "cuda:0" if torch.cuda.is_available() else "cpu"
print(f"[*] Target Device: {DEVICE} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})")

# 1. Load Model
print(f"[*] Loading model from {MODEL_DIR}...")
start_time = time.time()
model = ParlerTTSForConditionalGeneration.from_pretrained(
    MODEL_DIR,
    torch_dtype=torch.float32,
    low_cpu_mem_usage=True
).to(DEVICE)
model.eval()
load_time = time.time() - start_time
print(f"[✓] Model loaded in {load_time:.2f}s")

# 2. Load Tokenizers
print(f"[*] Loading tokenizers...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
desc_tokenizer = AutoTokenizer.from_pretrained(DESC_TOK_DIR if os.path.exists(DESC_TOK_DIR) else "google/flan-t5-large")
sampling_rate = getattr(model.config, "sampling_rate", 44100)
print(f"[✓] Tokenizers ready. Sampling rate: {sampling_rate} Hz")

# 3. Test Inputs
test_text = "नमस्ते! आपका स्वागत है। आज हम हिंदी में बात करेंगे।"
speaker = "Rohit"
description = "Rohit speaks with an expressive, articulate tone at a steady pace with clean audio quality and natural Hindi pronunciation."

print(f"[*] Input Text: '{test_text}'")
print(f"[*] Speaker: {speaker}")
print(f"[*] Description: '{description}'")

# 4. Tokenize with attention masks
desc_inputs = desc_tokenizer(description, return_tensors="pt")
input_ids = desc_inputs.input_ids.to(DEVICE)
attention_mask = desc_inputs.attention_mask.to(DEVICE)

prompt_inputs = tokenizer(test_text, return_tensors="pt")
prompt_input_ids = prompt_inputs.input_ids.to(DEVICE)
prompt_attention_mask = prompt_inputs.attention_mask.to(DEVICE)

# 5. Generate with inference mode
print("[*] Generating speech audio...")
gen_start = time.time()
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
gen_time = time.time() - gen_start

audio_arr = generation.cpu().numpy().squeeze()
if audio_arr.ndim > 1:
    audio_arr = audio_arr[0]

# Normalize
max_val = np.max(np.abs(audio_arr))
if max_val > 1.0:
    audio_arr = audio_arr / max_val * 0.98

duration = len(audio_arr) / sampling_rate
rtf = gen_time / duration if duration > 0 else 0

# 6. Save WAV
output_file = os.path.join(OUTPUT_DIR, "test_hindi_sample.wav")
sf.write(output_file, audio_arr, sampling_rate, format='WAV')

print(f"\n" + "=" * 60)
print(f"[✓] Synthesis Completed Successfully!")
print(f"• Output WAV: {output_file}")
print(f"• File Size: {os.path.getsize(output_file)} bytes ({os.path.getsize(output_file)/1024:.1f} KB)")
print(f"• Audio Duration: {duration:.2f} seconds")
print(f"• Generation Time: {gen_time:.2f} seconds (RTF: {rtf:.2f}x)")
print(f"• Sample Rate: {sampling_rate} Hz")
print(f"• Peak Amplitude: {np.max(np.abs(audio_arr)):.4f}")
print(f"• RMS Energy: {np.sqrt(np.mean(audio_arr**2)):.4f}")
print("=" * 60)
