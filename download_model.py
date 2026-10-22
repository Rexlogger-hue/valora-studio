"""
Model Downloader for AI4Bharat Indic-Parler-TTS
Downloads model weights and tokenizers locally to models/indic-parler-tts for offline execution.
"""
import os
import sys
from huggingface_hub import snapshot_download, HfFolder
from transformers import AutoTokenizer

LOCAL_MODEL_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "models", "indic-parler-tts"))
REPO_ID = "ai4bharat/indic-parler-tts"


def download_model(repo_id: str = REPO_ID, local_dir: str = LOCAL_MODEL_DIR):
    print("=" * 70)
    print(f"AI4Bharat Indic-Parler-TTS Setup & Model Downloader")
    print(f"Target Directory: {local_dir}")
    print(f"Repository: {repo_id}")
    print("=" * 70)
    
    token = HfFolder.get_token()
    if token:
        print("[✓] Hugging Face authentication token found.")
    else:
        print("[!] No Hugging Face token detected in environment.")
        print("[!] Note: ai4bharat/indic-parler-tts is a gated repository.")
        print("    1. Accept the model terms at: https://huggingface.co/ai4bharat/indic-parler-tts")
        print("    2. Login with your token using: .venv\\Scripts\\python.exe -c \"from huggingface_hub import login; login()\"")
        print()

    os.makedirs(local_dir, exist_ok=True)
    
    print(f"[*] Downloading snapshot from {repo_id}...")
    try:
        snapshot_download(
            repo_id=repo_id,
            local_dir=local_dir,
            local_dir_use_symlinks=False,
            token=token,
        )
        print(f"[✓] Model files downloaded successfully to: {local_dir}")
    except Exception as e:
        err_msg = str(e)
        if "401" in err_msg or "GatedRepoError" in err_msg or "restricted" in err_msg.lower():
            print("\n" + "!" * 70)
            print("[ERROR] Hugging Face Authentication / Access Required")
            print("The model 'ai4bharat/indic-parler-tts' requires accepting terms and authentication.")
            print("Steps to resolve:")
            print("  1. Visit: https://huggingface.co/ai4bharat/indic-parler-tts and click 'Agree and access repository'")
            print("  2. In your terminal, run:")
            print("     .\\.venv\\Scripts\\python.exe -c \"from huggingface_hub import login; login()\"")
            print("  3. Re-run this download script: .\\.venv\\Scripts\\python.exe download_model.py")
            print("!" * 70 + "\n")
            return False
        else:
            print(f"[ERROR] Failed to download model: {err_msg}")
            return False

    # Also download & cache description tokenizer
    print("[*] Caching text encoder / description tokenizer...")
    try:
        desc_tok_dir = os.path.join(local_dir, "description_tokenizer")
        os.makedirs(desc_tok_dir, exist_ok=True)
        # Standard description tokenizer for Parler-TTS is google/flan-t5-large
        desc_tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-large")
        desc_tokenizer.save_pretrained(desc_tok_dir)
        print(f"[✓] Description tokenizer cached to: {desc_tok_dir}")
    except Exception as e:
        print(f"[!] Note on description tokenizer: {e}")

    print("\n[✓] All required Indic-Parler-TTS assets are cached locally for offline execution.")
    return True


if __name__ == "__main__":
    success = download_model()
    sys.exit(0 if success else 1)
