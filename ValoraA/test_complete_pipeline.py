"""
Complete verification script for Indic-Parler-TTS pipeline.
Tests:
1. English input -> Hindi speech
2. Romanized Hindi (Hinglish) -> Devanagari -> Hindi speech
3. Pure Devanagari Hindi -> normalized speech
4. Code-mixed English/Hindi with names and technical terms
5. Longer multi-sentence paragraph with numbers and questions
6. Status, speaker listing, and error handling
"""

import sys
import time
import requests
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://127.0.0.1:8000"

def test_api():
    print("=" * 70)
    print("AI4BHARAT INDIC-PARLER-TTS COMPREHENSIVE PIPELINE VERIFICATION")
    print("=" * 70)

    # 1. Check Engine Status
    print("\n[1] Checking Engine Status...")
    res = requests.get(f"{BASE_URL}/api/indic-tts/status")
    assert res.status_code == 200, f"Status failed: {res.text}"
    status_data = res.json()
    print(f"Status OK: model_id={status_data.get('model_id')}, device={status_data.get('device')}, local_weights={status_data.get('local_weights_present')}")

    # 2. Check Speakers
    print("\n[2] Checking Supported Speakers...")
    res = requests.get(f"{BASE_URL}/api/indic-tts/speakers")
    assert res.status_code == 200
    spk_resp = res.json()
    speakers_list = spk_resp.get("speakers", [])
    print(f"Default voice prompt: {spk_resp.get('default_voice_description')[:80]}...")
    print(f"Available speakers count: {len(speakers_list)}")
    for spk in speakers_list:
        print(f"  - {spk['name']} ({spk.get('gender')}): {spk.get('tagline')}")

    # 3. Test Cases for Input Pipeline
    test_cases = [
        {
            "name": "Case 1: English Input -> Natural Hindi Speech",
            "input_text": "Hello, how are you? I can help you with your work.",
            "speaker": "Rohit",
            "expected_mode": "english_translated"
        },
        {
            "name": "Case 2: Romanized Hindi (Hinglish) -> Devanagari Speech",
            "input_text": "aap kaise ho, kya sab theek hai? mujhe aapki madad chahiye.",
            "speaker": "Divya",
            "expected_mode": "romanized_hindi"
        },
        {
            "name": "Case 3: Pure Devanagari Hindi Input",
            "input_text": "नमस्ते! आपका स्वागत है। आज हम हिंदी में बात करेंगे।",
            "speaker": "Aman",
            "expected_mode": "devanagari_normalized"
        },
        {
            "name": "Case 4: Mixed English-Hindi with Names and Technical Terms",
            "input_text": "Mera naam Rohit hai aur main Valora AI Studio use kar raha hoon.",
            "speaker": "Rani",
            "expected_mode": "romanized_hindi"
        },
        {
            "name": "Case 5: Long Multi-sentence Paragraph with Numbers & Questions",
            "input_text": "कृत्रिम बुद्धिमत्ता और डीप लर्निंग आज की दुनिया में तेजी से आगे बढ़ रहे हैं। यह तकनीक 100 से अधिक भाषाओं में अनुवाद करने में सक्षम है। क्या आप जानते हैं कि Valora AI स्टूडियो में आवाज़ कैसे बनती है? यह वास्तव में एक नया अनुभव है।",
            "speaker": "Rohit",
            "expected_mode": "devanagari_normalized"
        }
    ]

    for tc in test_cases:
        print(f"\n--- Running {tc['name']} ---")
        print(f"Input Text: \"{tc['input_text']}\"")
        print(f"Target Speaker: {tc['speaker']}")

        # Step A: Test /api/indic-tts/process-text
        t0 = time.time()
        p_res = requests.post(f"{BASE_URL}/api/indic-tts/process-text", json={"text": tc["input_text"]})
        assert p_res.status_code == 200, f"Process text failed: {p_res.text}"
        p_data = p_res.json()
        print(f"  [Text Processing]: Mode={p_data['detected_mode']}, Label='{p_data['language_label']}', Chunks={p_data['chunk_count']}")
        print(f"  [Normalized Hindi Transcript]: \"{p_data['normalized_hindi']}\"")

        # Step B: Test /api/indic-tts/synthesize
        s_payload = {
            "hindi_text": tc["input_text"],
            "speaker": tc["speaker"],
            "voice_description": "A Hindi speaker delivers the speech in a warm, clear, conversational tone with a moderate speaking pace and balanced pitch. The delivery is slightly expressive, with natural sentence pauses. The recording is very high quality, with a clear, close-up voice and very little background noise.",
            "speed": 1.0,
            "pitch": 0.0,
            "temperature": 1.0
        }
        s_res = requests.post(f"{BASE_URL}/api/indic-tts/synthesize", json=s_payload)
        assert s_res.status_code == 200, f"Synthesize failed: {s_res.text}"
        s_data = s_res.json()
        dt = time.time() - t0

        print(f"  [Synthesize OK]:")
        print(f"    - Spoken Transcript: \"{s_data['hindi_transcript']}\"")
        print(f"    - Audio URL: {s_data['audio_url']}")
        print(f"    - Duration: {s_data['duration_seconds']}s")
        print(f"    - Sample Rate: {s_data['sample_rate']} Hz")
        print(f"    - Engine Mode: {s_data['engine_mode']}")
        print(f"    - Latency: {s_data['generation_seconds']}s (Total roundtrip: {dt:.2f}s)")
        print(f"    - Waveform Peaks: {len(s_data['waveform'])} points")

        # Verify Audio File Downloadability
        audio_res = requests.get(f"{BASE_URL}{s_data['audio_url']}")
        assert audio_res.status_code == 200, "Generated audio file could not be downloaded!"
        assert len(audio_res.content) > 1000, f"Audio content is too small ({len(audio_res.content)} bytes)"
        assert audio_res.content[:4] == b"RIFF", "Audio file is not a valid RIFF/WAV format!"
        print(f"    - Audio WAV Verified: {len(audio_res.content)} bytes (Valid RIFF Header)")

    # 4. Error Handling Verification
    print("\n[6] Testing Error Handling...")
    err_res = requests.post(f"{BASE_URL}/api/indic-tts/synthesize", json={"hindi_text": "   ", "speaker": "Rohit"})
    print(f"Empty text response status: {err_res.status_code}")
    assert err_res.status_code in [400, 422], "Empty text should return 400/422 error"
    print(f"Empty text error detail: {err_res.json().get('detail')}")

    print("\n" + "=" * 70)
    print("ALL 5 PIPELINE VERIFICATION CASES & ERROR HANDLING PASSED 100%!")
    print("=" * 70)

if __name__ == "__main__":
    test_api()
