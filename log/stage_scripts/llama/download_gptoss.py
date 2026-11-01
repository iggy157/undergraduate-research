from huggingface_hub import snapshot_download
p = snapshot_download("openai/gpt-oss-120b", allow_patterns=["*.json", "*.safetensors", "tokenizer*", "LICENSE*", "*.txt", "*.jinja", "*.md"], max_workers=8)
print("DONE", p)
