# 数据库迁移脚本

## 文件说明

- `migrate_tables.sql` - SQL 迁移脚本，用于更新现有数据库表结构
- `import_syllabus_to_courses.py` - Python 脚本，将 syllabus.py 数据导入 courses 表

## 使用步骤

### 1. 迁移现有数据库表结构

如果数据库中已有旧结构的表，运行 SQL 迁移脚本：

```bash
mysql -u <用户名> -p<密码> <数据库名> < migrate_tables.sql
```

或登录 MySQL 后手动执行：

```bash
mysql -u <用户名> -p<密码>
USE <数据库名>;
SOURCE migrate_tables.sql;
```

### 2. 导入 syllabus 数据到 courses 表

```bash
cd backend/scripts
python import_syllabus_to_courses.py
```

这将把 syllabus.py 中的所有科目 - 年级 - 知识点导入到 courses 表中。

### 3. 新建数据库（可选）

如果是全新部署，直接运行：

```bash
python init_db.py
python scripts/import_syllabus_to_courses.py
```

## 表结构说明

### courses 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| subject | VARCHAR(50) | 科目（数学/英语/软考） |
| grade | INT | 年级 |
| kp | VARCHAR(500) | 知识点名称 |
| created_at | TIMESTAMP | 创建时间 |

### questions 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INT | 主键 |
| subject | VARCHAR(50) | 科目 |
| grade | INT | 年级 |
| kp | VARCHAR(500) | 知识点名称 |
| difficulty | VARCHAR(20) | 难度（basic/intermediate/advanced） |
| question | TEXT | 题目正文 |
| answer | VARCHAR(500) | 答案 |
| options | JSON | 选项（选择题） |
| explanation | TEXT | 解析 |
| question_type | VARCHAR(50) | 题目类型（MCQ/problem-solving） |
| created_at | TIMESTAMP | 创建时间 |

## API 变更

### POST /api/generate-question-batch

调用此 API 时，生成的 8 道题目会自动写入 questions 表。

请求示例：
```json
{
  "subject": "数学",
  "grade": 4,
  "kp_id": 0,
  "difficulty": "basic"
}
```
