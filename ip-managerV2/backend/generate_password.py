"""密码哈希生成工具

用法: python generate_password.py <你的密码>
将输出的哈希值复制到 config.yaml 的 password 字段
"""
import sys
import bcrypt

if len(sys.argv) != 2:
    print("用法: python generate_password.py <密码>")
    print("示例: python generate_password.py admin123")
    sys.exit(1)

password = sys.argv[1].encode('utf-8')
hashed = bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')
print(f"密码哈希: {hashed}")
print(f"请将此值复制到 config.yaml 的 auth.password 字段")
