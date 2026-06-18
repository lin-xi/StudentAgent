import base64
import os

from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from typing_extensions import Literal

SECRET_KEY = b"KsJ9tBOJf071HMRnIWrtHA=="  # AES-128 需要 16 字节密钥


def aes_encrypt(user_id: str) -> str:
    """加密 user_id，返回 Base64 编码的字符串（包含 IV）"""
    # 1. 生成随机 IV
    iv = os.urandom(AES.block_size)
    # 2. 创建 AES 密码器
    cipher = AES.new(SECRET_KEY, AES.MODE_CBC, iv)
    # 3. 加密数据（需要填充至块大小的倍数）
    encrypted_data = cipher.encrypt(pad(user_id.encode("utf-8"), AES.block_size))
    # 4. 将 IV 和密文拼接并转为 Base64
    iv_encrypted = iv + encrypted_data
    return base64.b64encode(iv_encrypted).decode("utf-8")


def aes_decrypt(encrypted_value: str) -> str:
    """解密 Base64 编码的字符串，返回原始 user_id"""
    # 1. 从 Base64 解码
    raw_data = base64.b64decode(encrypted_value)
    # 2. 提取 IV（前 16 字节）和密文
    iv = raw_data[: AES.block_size]
    encrypted_data = raw_data[AES.block_size :]
    # 3. 创建 AES 密码器并解密
    cipher = AES.new(SECRET_KEY, AES.MODE_CBC, iv)
    decrypted_data = unpad(cipher.decrypt(encrypted_data), AES.block_size)
    return decrypted_data.decode("utf-8")
