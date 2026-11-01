from huggingface_hub import snapshot_download
p = snapshot_download("meta-llama/Llama-3.3-70B-Instruct", allow_patterns=["*.json", "*.safetensors", "tokenizer*", "LICENSE*", "*.txt"], max_workers=8)
print("DONE", p)
