from huggingface_hub import snapshot_download
p = snapshot_download("openai/gpt-oss-120b", ignore_patterns=["original/*", "metal/*"], max_workers=8)
print("DONE", p)
