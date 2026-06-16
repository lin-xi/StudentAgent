-- 数据库迁移脚本：更新 courses 和 questions 表结构
-- 运行方式：mysql -u <user> -p <database> < migrate_tables.sql

-- 1. 修改 courses 表
-- 删除 syllabus_json 列，添加 kp 列
ALTER TABLE courses
    DROP COLUMN syllabus_json,
    ADD COLUMN kp VARCHAR(500) NOT NULL DEFAULT '' AFTER grade;

-- 修改唯一索引，包含 kp 字段
ALTER TABLE courses
    DROP INDEX unique_course,
    ADD UNIQUE INDEX unique_course (subject, grade, kp(255));

-- 2. 修改 questions 表
-- 重构为新结构
ALTER TABLE questions
    DROP COLUMN kp_id,
    ADD COLUMN kp VARCHAR(500) NOT NULL DEFAULT '' AFTER grade,
    DROP COLUMN question_json,
    ADD COLUMN question TEXT NOT NULL AFTER difficulty,
    ADD COLUMN answer VARCHAR(500) NOT NULL AFTER question,
    ADD COLUMN options JSON AFTER answer,
    ADD COLUMN explanation TEXT AFTER options,
    ADD COLUMN question_type VARCHAR(50) NOT NULL DEFAULT 'MCQ' AFTER explanation,
    ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP AFTER question_type;

-- 3. 验证表结构
DESCRIBE courses;
DESCRIBE questions;
