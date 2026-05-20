import os

bashrc_path = os.path.expanduser('~/.bashrc')
if os.path.exists(bashrc_path):
    with open(bashrc_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    old_line = "export OLLAMA_HOST=127.0.0.1:11434"
    new_line = "export OLLAMA_HOST=http://100.72.214.118:11434"
    
    if old_line in content:
        content = content.replace(old_line, new_line)
        with open(bashrc_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Successfully updated OLLAMA_HOST in ~/.bashrc to Tailscale IP!")
    elif new_line in content:
        print("OLLAMA_HOST is already pointing to Tailscale IP in ~/.bashrc.")
    else:
        # Append it if not present at all
        with open(bashrc_path, 'a', encoding='utf-8') as f:
            f.write(f"\n# GMC Ollama config (PC over Tailscale)\n{new_line}\n")
        print("Appended OLLAMA_HOST pointing to Tailscale IP in ~/.bashrc.")
else:
    print("~/.bashrc not found!")
