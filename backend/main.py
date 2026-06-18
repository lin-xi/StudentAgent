"""
FastAPI 后端主入口：导入所有路由并提供 API。
"""

# 导入 app 实例和所有路由模块（路由会自动注册到 app）
from agent_routes import *  # 出题与评估路由（原 main.py 中的路由）
from app import app
from auth import *  # 认证路由
from progress_routes import *  # 学习进度路由
from subject_grade_routes import *  # 学科年级路由
