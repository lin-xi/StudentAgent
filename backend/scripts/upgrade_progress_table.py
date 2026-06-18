"""
为现有 progress 表添加打卡相关字段。
"""
import os
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv

# 加载 .env 文件
env_path = f"{Path(__file__).resolve().parent.parent}/.env"
load_dotenv(dotenv_path=env_path)

# 数据库配置
DB_CONFIG = {
    "host": os.environ.get("MYSQL_HOST", "0.0.0.0"),
    "port": os.environ.get("MYSQL_PORT", "3306"),
    "user": os.environ.get("MYSQL_USER", "fake_user"),
    "password": os.environ.get("MYSQL_PASSWORD", "fake_password"),
    "database": os.environ.get("MYSQL_DATABASE", "fake_database"),
}

conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor()

# 检查字段是否存在并添加
fields_to_add = [
    ("check_in_records", "ALTER TABLE progress ADD COLUMN check_in_records JSON"),
    ("current_streak", "ALTER TABLE progress ADD COLUMN current_streak INT DEFAULT 0"),
    ("max_streak", "ALTER TABLE progress ADD COLUMN max_streak INT DEFAULT 0"),
    ("last_check_in_date", "ALTER TABLE progress ADD COLUMN last_check_in_date VARCHAR(20)"),
]

for field_name, sql in fields_to_add:
    cursor.execute("""
        SELECT COUNT(*) FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'progress' AND COLUMN_NAME = %s
    """, (DB_CONFIG["database"], field_name))
    count = cursor.fetchone()[0]

    if count == 0:
        print(f"添加字段 {field_name}...")
        cursor.execute(sql)
        print(f"  ✓ {field_name} 添加成功")
    else:
        print(f"字段 {field_name} 已存在，跳过")

conn.commit()
cursor.close()
conn.close()
print("数据库升级完成")
