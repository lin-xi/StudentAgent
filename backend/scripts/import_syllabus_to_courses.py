#!/usr/bin/env python3
"""
将 syllabus.py 中的大纲数据导入到 subjects, grades, subject_grade, courses 表中。
1. 先将学科名插入 subjects 表（已存在则跳过）
2. 将年级名插入 grades 表（已存在则跳过）
3. 在 subject_grade 表中建立关联（已存在则跳过）
4. 每个科目 - 年级 - 知识点对应一条课程记录（已存在则更新）
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


def import_syllabus_to_tables():
    """将 syllabus 数据导入到新表结构中，保留已有数据。"""
    conn = get_db_connection()
    cursor = conn.cursor()

    subject_id_map = {}
    grade_id_map = {}
    total_kp_count = 0
    insert_count = 0
    update_count = 0

    print("Step 1: 导入学科数据到 subjects 表...")
    for subject in SYLLABUS.keys():
        # 使用 INSERT IGNORE，已存在则跳过
        cursor.execute(
            """
            INSERT IGNORE INTO subjects (name) VALUES (%s)
        """,
            (subject,),
        )
        cursor.execute("SELECT id FROM subjects WHERE name = %s", (subject,))
        result = cursor.fetchone()
        if result:
            subject_id_map[subject] = result[0]
            print(f"  ✓ 学科：{subject} (id={subject_id_map[subject]})")

    print("\nStep 2: 导入年级数据到 grades 表...")
    all_grades = set()
    for grades in SYLLABUS.values():
        for grade in grades.keys():
            all_grades.add(grade)

    for grade in sorted(all_grades, key=lambda x: x):
        # 使用 INSERT IGNORE，已存在则跳过
        cursor.execute(
            """
            INSERT IGNORE INTO grades (name) VALUES (%s)
        """,
            (grade,),
        )
        cursor.execute("SELECT id FROM grades WHERE name = %s", (grade,))
        result = cursor.fetchone()
        if result:
            grade_id_map[grade] = result[0]
            print(f"  ✓ 年级：{grade} (id={grade_id_map[grade]})")

    print("\nStep 3: 建立学科年级关联到 subject_grade 表...")
    for subject, grades in SYLLABUS.items():
        subject_id = subject_id_map[subject]
        for grade in grades.keys():
            grade_id = grade_id_map[grade]
            # 使用 INSERT IGNORE，已存在则跳过
            cursor.execute(
                """
                INSERT IGNORE INTO subject_grade (subject_id, grade_id) VALUES (%s, %s)
            """,
                (subject_id, grade_id),
            )
            print(f"  ✓ {subject} - {grade}")

    print("\nStep 4: 导入课程数据到 courses 表（保留已有数据，更新重复数据）...")
    for subject, grades in SYLLABUS.items():
        subject_id = subject_id_map[subject]
        for grade, knowledge_points in grades.items():
            grade_id = grade_id_map[grade]

            for kp in knowledge_points:
                kp_name = kp["name"]

                # 使用 INSERT ... ON DUPLICATE KEY UPDATE
                # 如果 (subject_id, grade_id, kp) 唯一键冲突，则更新 kp 字段
                cursor.execute(
                    """
                    INSERT INTO courses (subject_id, grade_id, kp, created_at)
                    VALUES (%s, %s, %s, NOW())
                    ON DUPLICATE KEY UPDATE kp = VALUES(kp)
                """,
                    (subject_id, grade_id, kp_name),
                )

                total_kp_count += 1
                if cursor.rowcount == 1:
                    insert_count += 1
                elif cursor.rowcount == 2:
                    update_count += 1

                if total_kp_count % 50 == 0:
                    print(f"  已处理 {total_kp_count} 条课程记录...")

    conn.commit()
    cursor.close()
    conn.close()

    print(f"\n=== 导入完成 ===")
    print(f"  学科数：{len(subject_id_map)}")
    print(f"  年级数：{len(grade_id_map)}")
    print(
        f"  课程记录：共 {total_kp_count} 条，新增 {insert_count} 条，更新 {update_count} 条"
    )


if __name__ == "__main__":
    print("=== 开始导入 syllabus 数据到新表结构 ===\n")
    import_syllabus_to_tables()
    print("\n=== 导入完成！===")
