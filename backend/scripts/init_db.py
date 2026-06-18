#!/usr/bin/env python3
"""
数据库初始化脚本：创建数据库和表结构。
"""

import os
from pathlib import Path

import mysql.connector
from dotenv import load_dotenv
from mysql.connector import pooling

# 加载 .env 文件（优先于系统环境变量）
env_path = f"{Path(__file__).resolve().parent.parent}/.env"
load_dotenv(dotenv_path=env_path, override=True)

# 数据库配置（与管理配置一致）
DB_CONFIG = {
    "host": os.environ.get("MYSQL_HOST", "0.0.0.0"),
    "port": os.environ.get("MYSQL_PORT", "3306"),
    "user": os.environ.get("MYSQL_USER", "fake_user"),
    "password": os.environ.get("MYSQL_PASSWORD", "fake_password"),
}

DB_NAME = os.environ.get("MYSQL_DATABASE")


def create_database():
    """创建数据库（如果不存在）。"""
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute(
        f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
    )
    cursor.close()
    conn.close()
    print(f"数据库 '{DB_NAME}' 创建成功")


def init_tables():
    """初始化数据表结构。"""
    config = {**DB_CONFIG, "database": DB_NAME}
    conn = mysql.connector.connect(**config)
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
            kp VARCHAR(500) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY unique_course (subject, grade, kp(255))
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
            kp VARCHAR(500) NOT NULL,
            difficulty VARCHAR(20) NOT NULL,
            question TEXT NOT NULL,
            answer VARCHAR(500) NOT NULL,
            options JSON,
            explanation TEXT,
            question_type VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
    print("数据表初始化完成")


if __name__ == "__main__":
    print("开始初始化数据库...")
    create_database()
    init_tables()
    print("数据库初始化完成！")
