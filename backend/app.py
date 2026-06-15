"""
FastAPI 应用实例。
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 创建 app 实例
app = FastAPI(title="智能学习助手 API", version="1.2.0")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
