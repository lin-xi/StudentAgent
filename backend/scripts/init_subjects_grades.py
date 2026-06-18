"""
初始化 subjects, grades, subject_grade 表数据。
将现有 courses 表中的 subject 和 grade 数据迁移到新表。
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

print("=== 开始初始化学科年级数据 ===\n")

# 1. 从 courses 表提取唯一的 subject 和 grade 值
print("1. 从 courses 表提取唯一的 subject 和 grade...")
cursor.execute("SELECT DISTINCT subject, grade FROM courses")
courses_data = cursor.fetchall()

subjects = set()
grades = set()
subject_grade_pairs = set()

for subject, grade in courses_data:
    subjects.add(subject)
    grades.add(str(grade))
    subject_grade_pairs.add((subject, str(grade)))

print(f"   发现学科：{subjects}")
print(f"   发现年级：{grades}")

# 2. 插入 subjects 表
print("\n2. 插入 subjects 表...")
subject_id_map = {}
for subject in sorted(subjects):
    cursor.execute("""
        INSERT IGNORE INTO subjects (name) VALUES (%s)
    """, (subject,))
    cursor.execute("SELECT id FROM subjects WHERE name = %s", (subject,))
    subject_id_map[subject] = cursor.fetchone()[0]
    print(f"   ✓ {subject} (id={subject_id_map[subject]})")

# 3. 插入 grades 表
print("\n3. 插入 grades 表...")
grade_id_map = {}
for grade in sorted(grades, key=lambda x: int(x) if x.isdigit() else 0):
    # 数字年级转换为"X 年级"格式
    if grade.isdigit():
        grade_name = f"{grade}年级"
    else:
        grade_name = grade
    cursor.execute("""
        INSERT IGNORE INTO grades (name) VALUES (%s)
    """, (grade_name,))
    cursor.execute("SELECT id FROM grades WHERE name = %s", (grade_name,))
    grade_id_map[grade] = cursor.fetchone()[0]
    print(f"   ✓ {grade_name} (id={grade_id_map[grade]})")

# 4. 插入 subject_grade 关联表
print("\n4. 插入 subject_grade 关联表...")
for subject, grade in sorted(subject_grade_pairs):
    subject_id = subject_id_map[subject]
    grade_id = grade_id_map[grade]
    cursor.execute("""
        INSERT IGNORE INTO subject_grade (subject_id, grade_id) VALUES (%s, %s)
    """, (subject_id, grade_id))
    print(f"   ✓ {subject} + {grade}")

# 5. 更新 courses 表的 subject_id 和 grade_id 字段
print("\n5. 更新 courses 表，添加 subject_id 和 grade_id 字段...")

# 检查是否已有 subject_id 字段
cursor.execute("""
    SELECT COUNT(*) FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = %s AND TABLE_NAME = 'courses' AND COLUMN_NAME = 'subject_id'
""", (DB_CONFIG["database"],))
has_subject_id = cursor.fetchone()[0]

if has_subject_id == 0:
    # 添加新字段
    cursor.execute("ALTER TABLE courses ADD COLUMN subject_id INT")
    cursor.execute("ALTER TABLE courses ADD COLUMN grade_id INT")
    print("   ✓ 添加 subject_id 和 grade_id 字段")

# 更新 courses 表数据
cursor.execute("SELECT id, subject, grade FROM courses")
courses = cursor.fetchall()

for course_id, subject, grade in courses:
    subject_id = subject_id_map.get(subject)
    grade_str = str(grade)
    grade_name = f"{grade_str}年级" if grade_str.isdigit() else grade_str
    grade_id = grade_id_map.get(grade_str)

    if subject_id and grade_id:
        cursor.execute("""
            UPDATE courses SET subject_id = %s, grade_id = %s WHERE id = %s
        """, (subject_id, grade_id, course_id))
        print(f"   ✓ 更新 course id={course_id}: subject_id={subject_id}, grade_id={grade_id}")

# 6. 添加外键约束
print("\n6. 添加外键约束...")
try:
    cursor.execute("""
        ALTER TABLE courses
        ADD CONSTRAINT fk_courses_subject
        FOREIGN KEY (subject_id) REFERENCES subjects(id) ON DELETE CASCADE
    """)
    print("   ✓ 添加 subject_id 外键")
except Exception as e:
    print(f"   subject_id 外键可能已存在：{e}")

try:
    cursor.execute("""
        ALTER TABLE courses
        ADD CONSTRAINT fk_courses_grade
        FOREIGN KEY (grade_id) REFERENCES grades(id) ON DELETE CASCADE
    """)
    print("   ✓ 添加 grade_id 外键")
except Exception as e:
    print(f"   grade_id 外键可能已存在：{e}")

conn.commit()
cursor.close()
conn.close()

print("\n=== 初始化完成 ===")
