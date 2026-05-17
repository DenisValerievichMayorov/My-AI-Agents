import os

# Публичный ключ Windows-ПК (Antigravity)
PUBLIC_KEY = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQC+HVL4+Q6X0gbRxDZ4J+hk1WSKuL0t8M/UupnLFtCklRx+b8G0jwPIltYZD8y1fyEMYPC6NAOcLYqsoi42HzaQA9+P/cRsohj3SeDa+aVtotBeMcvhe0/5AZmQ1S1GR/PBIKn6oHiR25lvajrtsNGc/9TC/GhuvZnp8EQfVgO/TZ9y1kW5Jln1tTn872gGJMnzvQSbf4sRv3rxs6S9O12Os0G30NiDYp75MKo2q+NM7lt+ihRMOdwhqOLw5HTDG87gqYLdf4GLurHwOIM8FLlr2aH0N/ohPkIrgxc5HwqlEQaC3hA0FZwZkkY9CfOYNrb56PRo4RmDxZEBKzVDxts/Rk8IscLuhXbvQhhEm3D4/BV475uAXIjVCtsfrc4b8TSQFSejZiDdJGDQvYLceVckO/iIo8YBO5kuTs2hPTBKS/+XBQMO6nOmN1LNy7rV/Bez2uGgBL3utc352/9Q7rerPq5rXUevPfm40VLgqqVuCdzowNBm86fFk8FtNdLyhdjk+grzyTDZ7lMcXl9a+9c5wbPZsaGrms+uQhB8rZAkPeFGSgAsMAagg2B6sbhXygutgnQ7MFKOMWDjAldtfzIHhW93V79i4IlxGre5ill9fULLP+Qr+rbA3ex+OmbKFn8lrUmY5Rr/4BaI+LVLIRJr29U2Kn/YVuQQnCMqqMZ4Aw== anton@DESKTOP-85D3NJI"

ssh_dir = os.path.expanduser("~/.ssh")
auth_keys = os.path.join(ssh_dir, "authorized_keys")

os.makedirs(ssh_dir, exist_ok=True)

# Проверяем, не добавлен ли ключ уже
if os.path.exists(auth_keys):
    with open(auth_keys, 'r') as f:
        if PUBLIC_KEY in f.read():
            print("✅ Ключ уже установлен.")
            exit()

with open(auth_keys, 'a') as f:
    f.write("\n" + PUBLIC_KEY + "\n")

os.chmod(ssh_dir, 0o700)
os.chmod(auth_keys, 0o600)

print("✅ SSH ключ успешно установлен! Теперь ПК может входить без пароля.")
