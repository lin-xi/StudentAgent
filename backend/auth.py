"""
用户认证与滑动验证码 API。
"""

import hashlib
import os
import random
import re
import traceback
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from app import app
from database import get_connection
from fastapi import Cookie, HTTPException, Response
from pydantic import BaseModel, Field, field_validator
from utils import aes_decrypt, aes_encrypt

# ---------------------------------------------------------------------------
# 请求/响应模型
# ---------------------------------------------------------------------------


class ApiResponse(BaseModel):
    code: int
    error: str
    data: Any


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=8, max_length=20)
    confirm_password: str

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if not re.match(r"^[a-zA-Z0-9]+$", v):
            raise ValueError("密码只能包含英文字母和数字")
        return v

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v, info):
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("两次输入的密码不一致")
        return v


class LoginRequest(BaseModel):
    username: str
    password: str
    captcha_id: str  # 验证码 ID
    captcha_value: float  # 滑动验证码值 (0-1)


class CaptchaResponse(BaseModel):
    captcha_id: str
    target_value: float  # 目标值 (0-1)


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------


def hash_password(password: str) -> str:
    """对密码进行哈希加密。"""
    salt = os.environ.get("PASSWORD_SALT", "default_salt_change_me")
    return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()


def generate_captcha_id() -> str:
    """生成验证码 ID。"""
    return hashlib.md5(
        f"{datetime.now(timezone.utc).isoformat()}{random.random()}".encode()
    ).hexdigest()[:16]


# 简单的内存存储验证码（生产环境应用 Redis）
_captcha_store = {}


def cleanup_expired_captchas():
    """清理过期的验证码（超过 5 分钟）。"""
    now = datetime.now(timezone.utc)
    expired = [
        k
        for k, v in _captcha_store.items()
        if now - v["created"] > timedelta(minutes=5)
    ]
    for k in expired:
        del _captcha_store[k]


# ---------------------------------------------------------------------------
# API 端点
# ---------------------------------------------------------------------------


@app.get("/api/captcha", tags=["Auth"])
def get_captcha():
    """获取滑动验证码目标值。"""
    cleanup_expired_captchas()
    captcha_id = generate_captcha_id()
    target_value = round(random.uniform(0.4, 1.0), 2)  # 0.4-1 之间的随机值
    _captcha_store[captcha_id] = {
        "target_value": target_value,
        "created": datetime.now(timezone.utc),
    }
    return CaptchaResponse(captcha_id=captcha_id, target_value=target_value)


@app.post("/api/register", tags=["Auth"])
def register(req: RegisterRequest):
    """用户注册。"""
    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 检查用户名是否已存在
        cursor.execute("SELECT id FROM users WHERE username = %s", (req.username,))
        if cursor.fetchone():
            raise HTTPException(status_code=400, detail="用户名已存在")

        # 插入新用户
        password_hash = hash_password(req.password)
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
            (req.username, password_hash),
        )
        conn.commit()
        return {"message": "注册成功", "username": req.username}
    finally:
        cursor.close()
        conn.close()


@app.post("/api/login", tags=["Auth"])
def login(req: LoginRequest, response: Response):
    """用户登录。"""
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # 验证用户
        password_hash = hash_password(req.password)
        cursor.execute(
            "SELECT id, username FROM users WHERE username = %s AND password_hash = %s",
            (req.username, password_hash),
        )
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=401, detail="用户名或密码错误")

        # 验证滑动验证码
        captcha_data = _captcha_store.get(req.captcha_id)
        if not captcha_data:
            raise HTTPException(status_code=401, detail="验证码已过期或无效")

        # 检查验证码值是否匹配（允许 0.05 的误差）
        if abs(captcha_data["target_value"] - req.captcha_value) > 0.05:
            raise HTTPException(status_code=401, detail="验证码不正确")

        # 删除已使用的验证码
        del _captcha_store[req.captcha_id]

        # 设置 cookie（3 个月有效期）
        session_token = aes_encrypt(f"{user['id']}")
        expiry = datetime.now(timezone.utc) + timedelta(days=90)

        response.set_cookie(
            key="session_token",
            value=session_token,
            expires=expiry,
            httponly=True,
            samesite="lax",
        )

        # TODO: 将 session_token 存储到数据库以实现持久化会话

        return {
            "message": "登录成功",
            "user_id": user["id"],
            "username": user["username"],
        }
    finally:
        cursor.close()
        conn.close()


@app.post("/api/logout", tags=["Auth"])
def logout(response: Response):
    """用户登出。"""
    response.delete_cookie(key="session_token")
    return {"message": "登出成功"}


@app.get("/api/me", response_model=ApiResponse, tags=["Auth"])
def get_current_user(session_token: Optional[str] = Cookie(None)):
    """获取当前登录用户信息。"""
    if not session_token:
        return ApiResponse(
            code=401,
            error="未登录",
            data={},
        )
    else:
        user_id = aes_decrypt(session_token)
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(
                "SELECT user_id, subject_id, subject, grade_id, grade FROM user_subject_grade where user_id=%s",
                (user_id,),
            )
            info = cursor.fetchone()
            return ApiResponse(code=200, error="", data={**info} if info else {})
        except Exception as e:
            traceback.print_exc()
            return ApiResponse(
                code=500,
                error=str(e),
                data={},
            )
        finally:
            cursor.close()
            conn.close()
