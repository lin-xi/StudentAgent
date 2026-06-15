"""
FastAPI 后端主入口：导入所有路由并提供 API。
"""
# 导入 app 实例和所有路由模块（路由会自动注册到 app）
from app import app
from auth import *  # 认证路由
from agent_routes import *  # 出题与评估路由（原 main.py 中的路由）
