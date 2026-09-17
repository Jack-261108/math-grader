"""持久化错题知识库与艾宾浩斯抗遗忘复习调度引擎 (SQLite).

功能特性：
1. 结构化持久存储：历次速算练习册与行测答题卡批改错题自动沉淀到本地 SQLite (data/wrong_book.db)
2. 智能考点与错因聚类：自动映射二级考点（两期比重、削弱论证、除法截位等）与错因标签（粗心、概念混淆、蒙选）
3. 艾宾浩斯记忆遗忘曲线调度：1天、3天、7天、15天复习间隔，连续两次做对自动移入「已攻克」
4. 弱项专项重练组卷：按薄弱考点或待复习错题一键组装 15 题专项提分卷
"""

import hashlib
import json
import logging
import os
import sqlite3
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("wrong_book")

DB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "wrong_book.db")


def get_db_connection() -> sqlite3.Connection:
    """获取数据库连接并配置 Row 工厂"""
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_wrong_book_db() -> None:
    """初始化错题知识库数据表结构与索引"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 1. 错题主表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS wrong_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_uid TEXT UNIQUE NOT NULL,      -- 题目特征指纹哈希
            source_type TEXT NOT NULL,              -- 'omr' | 'math'
            source_task_id TEXT,                    -- 来源批改任务ID
            module_id TEXT NOT NULL,                -- 模块ID (如 data_analysis)
            module_name TEXT NOT NULL,              -- 模块名称 (如 资料分析)
            topic_category TEXT NOT NULL,           -- 二级核心考点 (如 两期比重)
            title TEXT,                             -- 题目标题或简述
            content_json TEXT NOT NULL,             -- 题目完整字段 JSON (算式、题干、选项等)
            user_answer TEXT,                       -- 最近一次错误选项或作答
            expected_answer TEXT,                   -- 正确标准答案
            error_tag TEXT DEFAULT 'confused',      -- 错因: careless | confused | guessing | calculation | unfamiliar
            user_notes TEXT DEFAULT '',             -- 用户复盘笔记
            wrong_count INTEGER DEFAULT 1,          -- 累计做错次数
            mastery_streak INTEGER DEFAULT 0,       -- 连续答对次数
            status TEXT DEFAULT 'reviewing',        -- 'reviewing' 学习复习中 | 'mastered' 已攻克
            review_stage INTEGER DEFAULT 0,         -- 艾宾浩斯阶段 (0~4)
            last_reviewed_at TEXT,                  -- 最近一次复习时间
            next_review_at TEXT NOT NULL,           -- 下次应复习日期 YYYY-MM-DD
            created_at TEXT NOT NULL,               -- 入库时间
            updated_at TEXT NOT NULL                -- 最近更新时间
        )
        """)

        # 2. 复习日志明细表
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS review_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER NOT NULL,
            reviewed_at TEXT NOT NULL,
            is_correct INTEGER NOT NULL,            -- 1: 对, 0: 错
            prev_stage INTEGER NOT NULL,
            new_stage INTEGER NOT NULL,
            user_input TEXT,
            FOREIGN KEY (question_id) REFERENCES wrong_questions(id) ON DELETE CASCADE
        )
        """)

        # 索引优化
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_wq_source ON wrong_questions(source_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_wq_status_due ON wrong_questions(status, next_review_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_wq_topic ON wrong_questions(topic_category)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_wq_module ON wrong_questions(module_id)")

        conn.commit()


# 初始化数据库
try:
    init_wrong_book_db()
except Exception as e:
    logger.error(f"[WrongBook] 数据库初始化失败: {e}")


# ============================================================
# 考点分类器与错因打标
# ============================================================

def categorize_topic(source_type: str, item: Dict[str, Any]) -> Tuple[str, str, str]:
    """智能推导题目所属的模块ID、模块名称与二级核心考点。

    返回: (module_id, module_name, topic_category)
    """
    if source_type == "math":
        expr = str(item.get("expression") or item.get("expr") or "").strip()
        err_type = str(item.get("error_type") or "")

        if "÷" in expr or "/" in expr or "div" in err_type:
            return "math_speed", "速算技巧", "速算-除法截位直除"
        elif "×" in expr or "*" in expr or "mul" in err_type:
            return "math_speed", "速算技巧", "速算-乘法拆分与尾数法"
        elif "+" in expr or "-" in expr or "borrow" in err_type or "carry" in err_type:
            return "math_speed", "速算技巧", "速算-高位直加直减与凑整"
        elif "%" in expr:
            return "math_speed", "速算技巧", "速算-两期比重与基期换算"
        else:
            return "math_speed", "速算技巧", "速算-四则心算基础"

    # 行测 OMR
    sec_id = str(item.get("section_id") or "general")
    sec_name = str(item.get("section_name") or "行测题目")
    stem = str(item.get("stem") or "")
    material = str(item.get("material") or "")
    full_text = stem + material

    if "资料" in sec_name or sec_id == "data_analysis":
        if "比重" in full_text:
            return "data_analysis", "资料分析", "资料分析-两期比重与现期比重"
        elif any(k in full_text for k in ["增长率", "增速", "增幅", "增长量"]):
            return "data_analysis", "资料分析", "资料分析-增长率计算与大小比较"
        elif any(k in full_text for k in ["基期", "上年", "往年"]):
            return "data_analysis", "资料分析", "资料分析-基期量与倍数差值"
        elif "平均" in full_text:
            return "data_analysis", "资料分析", "资料分析-平均数增幅与倍数"
        else:
            return "data_analysis", "资料分析", "资料分析-综合数据分析"

    elif "判断" in sec_name or sec_id == "reasoning":
        if any(k in full_text for k in ["削弱", "反驳", "质疑", "削弱上述"]):
            return "reasoning", "判断推理", "判断推理-削弱论证"
        elif any(k in full_text for k in ["加强", "支持", "前提", "假设"]):
            return "reasoning", "判断推理", "判断推理-加强论证"
        elif any(k in full_text for k in ["图形", "折纸", "立体", "展开图"]) or item.get("stem_images"):
            return "reasoning", "判断推理", "判断推理-图形推理"
        elif "定义" in full_text or "下列哪项符合" in full_text:
            return "reasoning", "判断推理", "判断推理-定义判断"
        elif "：" in stem or ":" in stem:
            return "reasoning", "判断推理", "判断推理-类比推理"
        else:
            return "reasoning", "判断推理", "判断推理-逻辑推理"

    elif "言语" in sec_name or sec_id == "verbal":
        if any(k in full_text for k in ["依次填入", "横线处", "成语", "词语"]):
            return "verbal", "言语理解", "言语理解-逻辑填空成语辨析"
        elif any(k in full_text for k in ["主旨", "主要", "意在", "核心", "文段意在说明"]):
            return "verbal", "言语理解", "言语理解-中心主旨题"
        elif any(k in full_text for k in ["排序", "连贯", "衔接"]):
            return "verbal", "言语理解", "言语理解-语句排序与衔接"
        elif "细节" in full_text or "下列说法符合" in full_text:
            return "verbal", "言语理解", "言语理解-细节理解题"
        else:
            return "verbal", "言语理解", "言语理解-片段阅读"

    elif "数量" in sec_name or sec_id == "quantity":
        if any(k in full_text for k in ["工程", "甲单独", "效率", "注水"]):
            return "quantity", "数量关系", "数量关系-工程问题"
        elif any(k in full_text for k in ["速度", "相向", "追及", "相遇", "里程"]):
            return "quantity", "数量关系", "数量关系-行程问题"
        elif any(k in full_text for k in ["概率", "几种方法", "排列", "组合", "选出"]):
            return "quantity", "数量关系", "数量关系-排列组合与概率"
        elif any(k in full_text for k in ["成本", "售价", "打折", "利润"]):
            return "quantity", "数量关系", "数量关系-经济利润问题"
        else:
            return "quantity", "数量关系", "数量关系-高频应用题"

    elif "政治" in sec_name or sec_id == "politics":
        return "politics", "政治理论", "政治理论-新思想与时政要点"

    elif "常识" in sec_name or sec_id == "common_sense":
        if any(k in full_text for k in ["法", "宪法", "行政", "诉讼", "条例"]):
            return "common_sense", "常识判断", "常识判断-法律常识"
        else:
            return "common_sense", "常识判断", "常识判断-文史综合常识"

    return sec_id, sec_name, f"{sec_name}-综合考点"


def derive_default_error_tag(source_type: str, item: Dict[str, Any]) -> str:
    """根据判题表现智能推断初始错因标签"""
    if source_type == "math":
        err = str(item.get("error_type") or "")
        if "negative" in err:
            return "careless"  # 粗心漏负号
        if "borrow" in err or "carry" in err:
            return "calculation"  # 借进位计算偏差
        if "division" in err or "overflow" in err:
            return "confused"  # 估商概念偏差
        return "calculation"

    # OMR
    quadrant = str(item.get("quadrant") or "")
    student_choice = item.get("student_choice")

    if not student_choice or str(student_choice).strip() in ["null", "None", ""]:
        return "guessing"  # 时间不足蒙题/漏涂
    if quadrant == "fast_loss":
        return "careless"  # 做题神速但做错：粗心审题
    if quadrant == "time_sink":
        return "confused"  # 超时死磕仍做错：考点混淆
    return "confused"


# ============================================================
# 艾宾浩斯记忆遗忘曲线调度核心
# ============================================================

EBBINGHAUS_INTERVAL_DAYS = {
    0: 1,   # 刚录入，次日第1次复习
    1: 3,   # 第1次做对，3天后第2次复习
    2: 7,   # 第2次做对，7天后第3次复习 (连续做对2次升级为已攻克)
    3: 15,  # 第3次做对，15天后终极巩固
    4: 30,  # 长期封存巩固
}


def compute_next_review_date(stage: int, from_date: Optional[datetime] = None) -> str:
    """根据复习阶段计算下一次应复习日期 (YYYY-MM-DD)"""
    base = from_date or datetime.now()
    days = EBBINGHAUS_INTERVAL_DAYS.get(stage, 1)
    target = base + timedelta(days=days)
    return target.strftime("%Y-%m-%d")


def compute_question_uid(source_type: str, item: Dict[str, Any]) -> str:
    """生成错题唯一特征指纹哈希（确保同题二次做错自动叠加快照）"""
    if source_type == "math":
        expr = str(item.get("expression") or item.get("expr") or "").strip()
        key = f"math:{expr}"
    else:
        q_num = item.get("q_num", 0)
        stem = str(item.get("stem") or "").strip()
        sec = item.get("section_id") or ""
        key = f"omr:{sec}:{q_num}:{stem[:80]}"
    return hashlib.md5(key.encode("utf-8")).hexdigest()


# ============================================================
# 增量入库主函数
# ============================================================

def ingest_wrong_question(
    source_type: str,
    source_task_id: str,
    item_data: Dict[str, Any],
    exam_title: str = ""
) -> int:
    """将单道做错的题目沉淀入库（支持去重与错误次数累加）。"""
    uid = compute_question_uid(source_type, item_data)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    next_due = compute_next_review_date(0)

    mod_id, mod_name, topic = categorize_topic(source_type, item_data)
    error_tag = derive_default_error_tag(source_type, item_data)

    if source_type == "math":
        title = f"速算算式: {item_data.get('expression') or item_data.get('expr')}"
        user_ans = str(item_data.get("student_raw") or item_data.get("student_val") or "")
        exp_ans = str(item_data.get("expected") or "")
    else:
        q_num = item_data.get("q_num", 1)
        title = f"{mod_name} 第 {q_num} 题"
        user_ans = str(item_data.get("student_choice") or "")
        exp_ans = str(item_data.get("std_choice") or "")

    # 包装完整快照 JSON
    item_snapshot = dict(item_data)
    item_snapshot["exam_title"] = exam_title
    item_snapshot["topic_category"] = topic
    content_json_str = json.dumps(item_snapshot, ensure_ascii=False)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, wrong_count, status, mastery_streak FROM wrong_questions WHERE question_uid = ?", (uid,))
        existing = cursor.fetchone()

        if existing:
            q_id = existing["id"]
            new_cnt = existing["wrong_count"] + 1
            # 重新做错，重置回待复习状态
            cursor.execute("""
            UPDATE wrong_questions
            SET wrong_count = ?,
                status = 'reviewing',
                review_stage = 0,
                mastery_streak = 0,
                user_answer = ?,
                content_json = ?,
                source_task_id = ?,
                next_review_at = ?,
                updated_at = ?
            WHERE id = ?
            """, (new_cnt, user_ans, content_json_str, source_task_id, next_due, now_str, q_id))
            conn.commit()
            return q_id
        else:
            cursor.execute("""
            INSERT INTO wrong_questions (
                question_uid, source_type, source_task_id, module_id, module_name,
                topic_category, title, content_json, user_answer, expected_answer,
                error_tag, user_notes, wrong_count, mastery_streak, status,
                review_stage, next_review_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                uid, source_type, source_task_id, mod_id, mod_name,
                topic, title, content_json_str, user_ans, exp_ans,
                error_tag, "", 1, 0, "reviewing",
                0, next_due, now_str, now_str
            ))
            conn.commit()
            return int(cursor.lastrowid or 0)


def ingest_batch_wrong_items(source_type: str, source_task_id: str, items: List[Dict[str, Any]], exam_title: str = "") -> int:
    """批量从判题报告中录入所有错题。"""
    count = 0
    for it in items:
        # math 判别
        if source_type == "math":
            if it.get("is_correct") is False and it.get("status") != "unknown":
                ingest_wrong_question(source_type, source_task_id, it, exam_title=exam_title)
                count += 1
        else:
            # omr 判别 (包含做错与漏答)
            if not it.get("is_correct"):
                ingest_wrong_question(source_type, source_task_id, it, exam_title=exam_title)
                count += 1
    return count


# ============================================================
# 查询与艾宾浩斯复习流调度
# ============================================================

def get_wrong_book_stats() -> Dict[str, Any]:
    """获取错题库全局宏观统计看板数据"""
    today_str = datetime.now().strftime("%Y-%m-%d")
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM wrong_questions")
        total_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM wrong_questions WHERE status = 'reviewing' AND next_review_at <= ?", (today_str,))
        today_due_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM wrong_questions WHERE status = 'mastered'")
        mastered_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM wrong_questions WHERE status = 'reviewing'")
        learning_count = cursor.fetchone()[0]

        # 模块分布统计
        cursor.execute("""
        SELECT module_name, COUNT(*) as count
        FROM wrong_questions
        GROUP BY module_name
        ORDER BY count DESC
        """)
        module_dist = [{"name": row["module_name"], "count": row["count"]} for row in cursor.fetchall()]

        # 核心薄弱考点 TOP 5
        cursor.execute("""
        SELECT topic_category, COUNT(*) as count, SUM(wrong_count) as total_wrongs
        FROM wrong_questions
        GROUP BY topic_category
        ORDER BY count DESC, total_wrongs DESC
        LIMIT 6
        """)
        topic_ranking = [{"topic": row["topic_category"], "count": row["count"], "total_wrongs": row["total_wrongs"]} for row in cursor.fetchall()]

        # 错因分布统计
        cursor.execute("""
        SELECT error_tag, COUNT(*) as count
        FROM wrong_questions
        GROUP BY error_tag
        """)
        tag_dist = {row["error_tag"]: row["count"] for row in cursor.fetchall()}

    return {
        "total_count": total_count,
        "today_due_count": today_due_count,
        "mastered_count": mastered_count,
        "learning_count": learning_count,
        "module_dist": module_dist,
        "topic_ranking": topic_ranking,
        "tag_dist": tag_dist,
        "today_str": today_str
    }


def query_wrong_questions(
    source_type: Optional[str] = None,
    status: Optional[str] = None,
    topic: Optional[str] = None,
    error_tag: Optional[str] = None,
    only_due: bool = False,
    keyword: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> Dict[str, Any]:
    """多维度灵活筛选错题列表"""
    today_str = datetime.now().strftime("%Y-%m-%d")
    clauses = []
    params = []

    if source_type and source_type != "all":
        clauses.append("source_type = ?")
        params.append(source_type)

    if status and status != "all":
        clauses.append("status = ?")
        params.append(status)

    if topic and topic != "all":
        clauses.append("topic_category = ?")
        params.append(topic)

    if error_tag and error_tag != "all":
        clauses.append("error_tag = ?")
        params.append(error_tag)

    if only_due:
        clauses.append("status = 'reviewing' AND next_review_at <= ?")
        params.append(today_str)

    if keyword:
        clauses.append("(title LIKE ? OR content_json LIKE ? OR topic_category LIKE ?)")
        kw = f"%{keyword.strip()}%"
        params.extend([kw, kw, kw])

    where_sql = ("WHERE " + " AND ".join(clauses)) if clauses else ""

    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 总记录数
        cursor.execute(f"SELECT COUNT(*) FROM wrong_questions {where_sql}", params)
        total = cursor.fetchone()[0]

        # 结果集
        cursor.execute(f"""
        SELECT * FROM wrong_questions
        {where_sql}
        ORDER BY
            CASE WHEN status = 'reviewing' AND next_review_at <= '{today_str}' THEN 0 ELSE 1 END,
            next_review_at ASC,
            wrong_count DESC,
            updated_at DESC
        LIMIT ? OFFSET ?
        """, (*params, limit, offset))

        rows = cursor.fetchall()
        questions = []
        for r in rows:
            it = dict(r)
            try:
                it["content"] = json.loads(it["content_json"])
            except Exception:
                it["content"] = {}
            it["is_due"] = bool(it["status"] == "reviewing" and it["next_review_at"] <= today_str)
            questions.append(it)

    return {
        "total": total,
        "questions": questions,
        "today_str": today_str
    }


def record_review_result(question_id: int, is_correct: bool, user_input: str = "") -> Dict[str, Any]:
    """记录一次复习并按照艾宾浩斯遗忘曲线递延周期。

    规则：
    1. 做对：推进到下一阶段，连续答对 streak + 1；若 streak >= 2，直接升级为 'mastered'（已攻克）！
    2. 做错：复位至 Stage 1，streak 清零，次日重新复习。
    """
    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d %H:%M:%S")

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM wrong_questions WHERE id = ?", (question_id,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"错题 ID {question_id} 不存在")

        cur_stage = row["review_stage"]
        cur_streak = row["mastery_streak"]

        if is_correct:
            new_streak = cur_streak + 1
            new_stage = min(4, cur_stage + 1)
            # 连续答对2次直接算攻克
            if new_streak >= 2 or new_stage >= 4:
                new_status = "mastered"
                # 攻克后放宽至30天巩固
                next_due = (now + timedelta(days=30)).strftime("%Y-%m-%d")
            else:
                new_status = "reviewing"
                next_due = compute_next_review_date(new_stage, from_date=now)
        else:
            new_streak = 0
            new_stage = 1  # 退回第1阶段
            new_status = "reviewing"
            next_due = (now + timedelta(days=1)).strftime("%Y-%m-%d")

        cursor.execute("""
        UPDATE wrong_questions
        SET review_stage = ?,
            mastery_streak = ?,
            status = ?,
            last_reviewed_at = ?,
            next_review_at = ?,
            updated_at = ?
        WHERE id = ?
        """, (new_stage, new_streak, new_status, now_str, next_due, now_str, question_id))

        # 插入日志
        cursor.execute("""
        INSERT INTO review_logs (question_id, reviewed_at, is_correct, prev_stage, new_stage, user_input)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (question_id, now_str, 1 if is_correct else 0, cur_stage, new_stage, user_input))

        conn.commit()

    return {
        "question_id": question_id,
        "is_correct": is_correct,
        "new_stage": new_stage,
        "mastery_streak": new_streak,
        "status": new_status,
        "next_review_at": next_due
    }


def update_question_tag_or_notes(question_id: int, error_tag: Optional[str] = None, user_notes: Optional[str] = None) -> bool:
    """更新错题的错因标签或个人复盘笔记"""
    updates = []
    params = []
    if error_tag:
        updates.append("error_tag = ?")
        params.append(error_tag)
    if user_notes is not None:
        updates.append("user_notes = ?")
        params.append(user_notes)

    if not updates:
        return False

    updates.append("updated_at = ?")
    params.append(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    params.append(question_id)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE wrong_questions SET {', '.join(updates)} WHERE id = ?", params)
        conn.commit()
    return True


# ============================================================
# 针对性弱项重练组卷中心
# ============================================================

def generate_weakness_practice_sheet(
    topic_list: Optional[List[str]] = None,
    source_type: Optional[str] = None,
    only_due: bool = False,
    recent_days: Optional[int] = None,
    count: int = 15
) -> Dict[str, Any]:
    """一键组装针对性薄弱考点自测提分卷（默认15题黄金题量）。"""
    today_str = datetime.now().strftime("%Y-%m-%d")
    clauses = ["status != 'mastered'"]
    params: List[Any] = []

    if source_type and source_type != "all":
        clauses.append("source_type = ?")
        params.append(source_type)

    if topic_list and len(topic_list) > 0:
        placeholders = ",".join("?" for _ in topic_list)
        clauses.append(f"topic_category IN ({placeholders})")
        params.extend(topic_list)

    if only_due:
        clauses.append("next_review_at <= ?")
        params.append(today_str)

    if recent_days and recent_days > 0:
        since_date = (datetime.now() - timedelta(days=recent_days)).strftime("%Y-%m-%d 00:00:00")
        clauses.append("created_at >= ?")
        params.append(since_date)

    where_sql = "WHERE " + " AND ".join(clauses)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        # 优先抽取待复习、做错次数高的核心薄弱题目
        cursor.execute(f"""
        SELECT * FROM wrong_questions
        {where_sql}
        ORDER BY
            CASE WHEN next_review_at <= '{today_str}' THEN 0 ELSE 1 END,
            wrong_count DESC,
            RANDOM()
        LIMIT ?
        """, (*params, count))

        rows = cursor.fetchall()
        sheet_items = []
        for idx, r in enumerate(rows, start=1):
            it = dict(r)
            try:
                c = json.loads(it["content_json"])
            except Exception:
                c = {}

            sheet_items.append({
                "sheet_q_num": idx,
                "db_question_id": it["id"],
                "source_type": it["source_type"],
                "module_name": it["module_name"],
                "topic_category": it["topic_category"],
                "expression": c.get("expression") or c.get("expr"),
                "stem": c.get("stem") or it["title"],
                "options": c.get("options") or {},
                "material": c.get("material"),
                "stem_images": c.get("stem_images") or [],
                "expected_answer": it["expected_answer"],
                "user_last_answer": it["user_answer"],
                "error_name": c.get("error_name") or it["error_tag"],
                "diagnosis": c.get("diagnosis"),
                "advice": c.get("advice") or c.get("tip"),
                "row_num": c.get("row_num"),
                "col_idx": c.get("col_idx"),
                "score_per_q": c.get("score_per_q", 1.0)
            })

    title = "针对性薄弱考点提分重练卷"
    if topic_list and len(topic_list) == 1:
        title = f"【{topic_list[0]}】专项突击重练卷"
    elif only_due:
        title = f"艾宾浩斯【今日待复习】攻坚重练卷 ({len(sheet_items)}题)"

    return {
        "title": title,
        "total_items": len(sheet_items),
        "target_count": count,
        "items": sheet_items,
        "created_date": today_str
    }
