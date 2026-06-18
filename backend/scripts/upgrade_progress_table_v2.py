"""
升级 progress 表结构到新版本。
新表结构：
- id: 自增主键
- user_id: 用户 ID
- kp_level: 难度等级 ('basic', 'intermediate', 'advanced')
- check_in: 该难度等级是否打卡完成 (BOOLEAN)
- wrong_count: 第一次提交的错题数量
- check_in_date: 该难度等级完成时间 (VARCHAR)
- subject_id: 科目 ID (外键)
- grade_id: 年级 ID (外键)
- course_id: 课程 ID/KP ID (外键)

旧字段将被删除：
- completed_kp_count
- kp_progress
- overall_complete
- check_in_records
- current_streak
- max_streak
- last_check_in_date
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

print("=== 开始升级 progress 表结构 ===\n")

# 1. 备份旧数据（如果需要）
print("1. 备份旧数据到 progress_backup 表...")
try:
    cursor.execute("DROP TABLE IF EXISTS progress_backup")
    cursor.execute("CREATE TABLE progress_backup AS SELECT * FROM progress")
    print("   ✓ 备份完成")
except Exception as e:
    print(f"   备份失败（可能原表不存在）: {e}")

# 2. 删除旧表
print("\n2. 删除旧 progress 表...")
try:
    cursor.execute("DROP TABLE IF EXISTS progress")
    print("   ✓ 旧表已删除")
except Exception as e:
    print(f"   删除失败：{e}")

# 3. 创建新表结构
print("\n3. 创建新 progress 表结构...")
cursor.execute("""
    CREATE TABLE progress (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        kp_level VARCHAR(20) NOT NULL,
        check_in BOOLEAN DEFAULT FALSE,
        wrong_count INT DEFAULT 0,
        check_in_date VARCHAR(20),
        subject_id INT NOT NULL,
        grade_id INT NOT NULL,
        course_id INT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
        FOREIGN KEY (grade_id) REFERENCES grades(id) ON DELETE CASCADE,
        FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
        UNIQUE KEY unique_progress (user_id, subject_id, grade_id, course_id, kp_level)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
""")
print("   ✓ 新表创建完成")

conn.commit()
cursor.close()
conn.close()

print("\n=== 升级完成 ===")
print("注意：旧数据已备份到 progress_backup 表，确认新系统运行正常后可手动删除")
