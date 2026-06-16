#!/usr/bin/env python3
"""
将 syllabus.py 中的大纲数据导入到 courses 表中。
每个科目 - 年级 - 知识点对应一条课程记录。
"""

import os
import sys
from pathlib import Path

# 添加 backend 目录到路径
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from dotenv import load_dotenv
from syllabus import SYLLABUS

# 加载 .env 文件
env_path = backend_dir / ".env"
load_dotenv(dotenv_path=env_path, override=True)

import mysql.connector


def get_db_connection():
    """获取数据库连接。"""
    return mysql.connector.connect(
        host=os.environ.get("MYSQL_HOST", "0.0.0.0"),
        port=os.environ.get("MYSQL_PORT", "3306"),
        user=os.environ.get("MYSQL_USER", "fake_user"),
        password=os.environ.get("MYSQL_PASSWORD", "fake_password"),
        database=os.environ.get("MYSQL_DATABASE", "fake_database"),
    )


def import_syllabus_to_courses():
    """将 syllabus 数据导入 courses 表。"""
    conn = get_db_connection()
    cursor = conn.cursor()

    total_count = 0

    for subject, grades in SYLLABUS.items():
        for grade, knowledge_points in grades.items():
            for kp in knowledge_points:
                kp_id = kp["id"]
                kp_name = kp["name"]

                # 插入课程记录（使用 ON DUPLICATE KEY UPDATE 避免重复）
                cursor.execute("""
                    INSERT INTO courses (subject, grade, kp, created_at)
                    VALUES (%s, %s, %s, NOW())
                    ON DUPLICATE KEY UPDATE kp = VALUES(kp)
                """, (subject, grade, kp_name))

                total_count += 1

                if total_count % 50 == 0:
                    print(f"已导入 {total_count} 条记录...")

    conn.commit()
    cursor.close()
    conn.close()

    print(f"导入完成！共导入 {total_count} 条课程记录。")


if __name__ == "__main__":
    print("开始导入 syllabus 数据到 courses 表...")
    import_syllabus_to_courses()
    print("导入完成！")
