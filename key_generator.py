import secrets
# 生成一个 32 字节的密钥
secure_key = secrets.token_hex(32)
print("Your Secure Key:", secure_key)
