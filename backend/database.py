"""
MySQL 数据库连接与表结构定义。
"""

import os
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import pooling

# 加载 .env 文件（优先于系统环境变量）
env_path = f"{Path(__file__).resolve().parent}/.env"
load_dotenv(dotenv_path=env_path, override=True)

# 数据库配置（与管理配置一致）
DB_CONFIG = {
    "host": os.environ.get("MYSQL_HOST", "0.0.0.0"),
    "port": os.environ.get("MYSQL_PORT", "3306"),
    "user": os.environ.get("MYSQL_USER", "fake_user"),
    "password": os.environ.get("MYSQL_PASSWORD", "fake_password"),
    "database": os.environ.get("MYSQL_DATABASE", "fake_database"),
}

# 创建连接池
connection_pool = pooling.MySQLConnectionPool(
    pool_name="student_agent_pool", pool_size=2, **DB_CONFIG
)


def get_connection():
    """从连接池获取数据库连接。"""
    return connection_pool.get_connection()


def init_tables():
    """初始化数据库表结构。"""
    conn = get_connection()
    cursor = conn.cursor()

    # 用户表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    # 课程表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id INT AUTO_INCREMENT PRIMARY KEY,
            subject VARCHAR(50) NOT NULL,
            grade INT NOT NULL,
            syllabus_json JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_course (subject, grade)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    # 学习进度表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS progress (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            course_id INT NOT NULL,
            completed_kp_count INT DEFAULT 0,
            kp_progress JSON,
            overall_complete BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE,
            UNIQUE KEY unique_progress (user_id, course_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    # 问题表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            subject VARCHAR(50) NOT NULL,
            grade INT NOT NULL,
            kp_id INT NOT NULL,
            difficulty VARCHAR(20) NOT NULL,
            question_json JSON NOT NULL,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    # 错题表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mistakes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            question_id INT NOT NULL,
            user_answer VARCHAR(500),
            correct_answer VARCHAR(500),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("数据库表初始化完成")


if __name__ == "__main__":
    init_tables()
