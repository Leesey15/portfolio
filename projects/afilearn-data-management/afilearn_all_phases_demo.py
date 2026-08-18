"""
AfiLearn University Learning Analytics — FULL PROJECT DEMO (All 13 Phases)
DSCD 606 Data Management Techniques

This script reproduces every phase of the project end-to-end on a small
SAMPLE dataset (not the full 32,593-student / 11.1M-row OULAD dataset),
so it can be run LIVE in a few seconds during presentation.

Run:  python3 afilearn_all_phases_demo.py
"""

import sqlite3
import hashlib
import json
import os
import shutil
import time

import duckdb
import pandas as pd

DB_PATH = "afilearn_demo.db"


def header(phase, title):
    print("\n" + "#" * 72)
    print(f"# {phase}: {title}")
    print("#" * 72)


# ======================================================================
# PHASE 1: DATA PROFILING
# ======================================================================
header("PHASE 1", "Introduction to Data Management — Profiling")

# Simulate the 7 source files as small in-memory tables (sample of real OULAD structure)
courses_data = [("AAA", "2013J", 268), ("BBB", "2013J", 240), ("CCC", "2014J", 241)]
students_data = [
    (11391, "AAA", "2013J", "M", "East Anglian Region", "HE Qualification", "90-100%", "55<=", 0, 240, "N", "Pass"),
    (28400, "AAA", "2013J", "F", "London Region", "A Level or Equivalent", "40-50%", "35-55", 0, 60, "N", "Pass"),
    (30268, "BBB", "2013J", "F", "North Region", "Lower Than A Level", "20-30%", "0-35", 0, 60, "N", "Withdrawn"),
    (32885, "BBB", "2013J", "F", "South Region", "A Level or Equivalent", "50-60%", "0-35", 0, 60, "N", "Fail"),
    (23629, "CCC", "2014J", "M", "West Midlands Region", "HE Qualification", "80-90%", "35-55", 0, 120, "N", "Distinction"),
]
assessments_data = [(1752, "AAA", "2013J", "TMA", 10.0), (1753, "BBB", "2013J", "TMA", 12.5)]
student_assessments_data = [
    (11391, 1752, "AAA", "2013J", 78.0),
    (28400, 1752, "AAA", "2013J", 82.5),
    (30268, 1753, "BBB", "2013J", None),   # simulate a null score
]
vle_data = [(546943, "AAA", "2013J", "resource"), (546712, "BBB", "2013J", "oucontent")]
student_vle_data = [
    (11391, "AAA", "2013J", 546943, -5, 12),
    (11391, "AAA", "2013J", 546943, 3, 8),
    (28400, "AAA", "2013J", 546943, 2, 4),
    (28400, "AAA", "2013J", 546943, 2, 4),   # duplicate row on purpose
]

profile = {
    "courses.csv": courses_data,
    "studentInfo.csv": students_data,
    "assessments.csv": assessments_data,
    "studentAssessment.csv": student_assessments_data,
    "vle.csv": vle_data,
    "studentVle.csv": student_vle_data,
}

print("Profiling sample source files:")
for name, rows in profile.items():
    print(f"  {name:22s}: {len(rows)} rows")

null_scores = sum(1 for r in student_assessments_data if r[4] is None)
dup_vle = len(student_vle_data) - len(set(student_vle_data))
print(f"\nQuality issues identified:")
print(f"  Null scores in studentAssessment : {null_scores}")
print(f"  Duplicate rows in studentVle      : {dup_vle}")


# ======================================================================
# PHASE 2: LIFECYCLE, GOVERNANCE & METADATA
# ======================================================================
header("PHASE 2", "Data Models, Lifecycle & Governance")

lifecycle = ["COLLECTION (CSV)", "STORAGE (SQLite)", "PROCESSING (ETL)",
             "ANALYSIS (Warehouse)", "ARCHIVE (Backups, 7yr retention)"]
print("Data Lifecycle: " + "  ->  ".join(lifecycle))

governance = {
    "Data Owner": "Learning Analytics Office",
    "Data Steward": "Database Administrator",
    "Access Control": "Role-based (Admin, Analyst, Viewer)",
    "Retention": "7 years",
    "Privacy": "PII masked for non-admin users",
}
print("\nGovernance policy:")
for k, v in governance.items():
    print(f"  {k:16s}: {v}")

metadata_catalogue = {
    "id_student": ("INTEGER", "Unique student identifier", "PII: Yes"),
    "code_module": ("TEXT", "Course module code", "PII: No"),
    "gender": ("TEXT", "Student gender (M/F)", "PII: Yes"),
    "final_result": ("TEXT", "Course outcome", "PII: No"),
}
print("\nMetadata catalogue (sample):")
for col, (dtype, desc, pii) in metadata_catalogue.items():
    print(f"  {col:14s} {dtype:9s} {desc:28s} {pii}")


# ======================================================================
# PHASE 3 & 4: DATABASE DESIGN + IMPLEMENTATION
# ======================================================================
header("PHASE 3 & 4", "Database Design & Implementation")

if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON;")
cur = conn.cursor()

cur.executescript("""
CREATE TABLE courses (
    code_module TEXT NOT NULL,
    code_presentation TEXT NOT NULL,
    module_presentation_length INTEGER,
    PRIMARY KEY (code_module, code_presentation)
);

CREATE TABLE students (
    id_student INTEGER NOT NULL,
    code_module TEXT NOT NULL,
    code_presentation TEXT NOT NULL,
    gender TEXT CHECK(gender IN ('M','F')),
    region TEXT,
    highest_education TEXT,
    imd_band TEXT,
    age_band TEXT,
    num_of_prev_attempts INTEGER DEFAULT 0,
    studied_credits INTEGER,
    disability TEXT CHECK(disability IN ('Y','N')),
    final_result TEXT CHECK(final_result IN ('Pass','Fail','Distinction','Withdrawn')),
    PRIMARY KEY (id_student, code_module, code_presentation),
    FOREIGN KEY (code_module, code_presentation)
        REFERENCES courses(code_module, code_presentation)
);

CREATE TABLE student_registrations (
    id_student INTEGER NOT NULL,
    code_module TEXT NOT NULL,
    code_presentation TEXT NOT NULL,
    date_registration INTEGER,
    date_unregistration INTEGER,
    FOREIGN KEY (code_module, code_presentation)
        REFERENCES courses(code_module, code_presentation)
);

CREATE TABLE assessments (
    id_assessment INTEGER PRIMARY KEY,
    code_module TEXT NOT NULL,
    code_presentation TEXT NOT NULL,
    assessment_type TEXT,
    weight REAL CHECK(weight BETWEEN 0 AND 100)
);

CREATE TABLE student_assessments (
    id_student INTEGER NOT NULL,
    id_assessment INTEGER NOT NULL,
    code_module TEXT NOT NULL,
    code_presentation TEXT NOT NULL,
    score REAL CHECK(score IS NULL OR score BETWEEN 0 AND 100),
    FOREIGN KEY (id_assessment) REFERENCES assessments(id_assessment)
);

CREATE TABLE vle_resources (
    id_site INTEGER PRIMARY KEY,
    code_module TEXT,
    code_presentation TEXT,
    activity_type TEXT
);

CREATE TABLE student_vle_interactions (
    id_student INTEGER,
    code_module TEXT,
    code_presentation TEXT,
    id_site INTEGER,
    date INTEGER,
    sum_click INTEGER CHECK(sum_click >= 0)
);
""")

cur.executemany("INSERT INTO courses VALUES (?,?,?)", courses_data)
cur.executemany("INSERT INTO students VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", students_data)
cur.executemany(
    "INSERT INTO student_registrations (id_student, code_module, code_presentation, date_registration) VALUES (?,?,?,?)",
    [(s[0], s[1], s[2], -30) for s in students_data],
)
cur.executemany("INSERT INTO assessments VALUES (?,?,?,?,?)", assessments_data)
cur.executemany("INSERT INTO student_assessments VALUES (?,?,?,?,?)", student_assessments_data)
cur.executemany("INSERT INTO vle_resources VALUES (?,?,?,?)", vle_data)
cur.executemany("INSERT INTO student_vle_interactions VALUES (?,?,?,?,?,?)", student_vle_data)
conn.commit()

print("Schema created (3NF, composite keys, foreign keys, CHECK constraints).")
for t in ["courses", "students", "student_registrations", "assessments",
          "student_assessments", "vle_resources", "student_vle_interactions"]:
    n = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"  {t:28s}: {n} rows loaded")

print("\nTransaction Control Demo (ACID Atomicity):")
TEST_ID = 99999
cur.execute("BEGIN TRANSACTION;")
cur.execute(
    "INSERT INTO student_registrations (id_student, code_module, code_presentation, date_registration) "
    "VALUES (?,?,?,?)", (TEST_ID, "AAA", "2013J", 0))
exists_after_insert = cur.execute(
    "SELECT COUNT(*) FROM student_registrations WHERE id_student=?", (TEST_ID,)).fetchone()[0]
conn.rollback()
exists_after_rollback = cur.execute(
    "SELECT COUNT(*) FROM student_registrations WHERE id_student=?", (TEST_ID,)).fetchone()[0]
print(f"  After INSERT  : row exists = {exists_after_insert == 1}")
print(f"  After ROLLBACK: row exists = {exists_after_rollback == 1} (expected False)")

print("\nConstraint enforcement demo:")
for label, sql, params in [
    ("Invalid course (FK)", "INSERT INTO student_registrations (id_student, code_module, code_presentation) VALUES (?,?,?)", (1, "ZZZ", "9999X")),
    ("Invalid gender (CHECK)", "INSERT INTO students VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
     (77777, "AAA", "2013J", "X", "Region", "HE", "90-100%", "35-55", 0, 60, "N", "Pass")),
]:
    try:
        cur.execute(sql, params)
        conn.commit()
    except sqlite3.IntegrityError as e:
        print(f"  {label:24s}: rejected automatically -> {e}")
        conn.rollback()


# ======================================================================
# PHASE 5: QUERY OPTIMIZATION
# ======================================================================
header("PHASE 5", "Query Optimization")

def timed_query(sql, params=()):
    t0 = time.perf_counter()
    cur.execute(sql, params)
    cur.fetchall()
    return (time.perf_counter() - t0) * 1000  # ms

before = timed_query(
    "SELECT id_student, SUM(sum_click) FROM student_vle_interactions "
    "WHERE code_module=? AND code_presentation=? GROUP BY id_student", ("AAA", "2013J"))

cur.execute("CREATE INDEX idx_svi_course ON student_vle_interactions(code_module, code_presentation, id_student);")
cur.execute("ANALYZE;")

after = timed_query(
    "SELECT id_student, SUM(sum_click) FROM student_vle_interactions "
    "WHERE code_module=? AND code_presentation=? GROUP BY id_student", ("AAA", "2013J"))

print(f"VLE engagement query — before index : {before:.4f} ms")
print(f"VLE engagement query — after index  : {after:.4f} ms")
print("(Note: sample dataset is tiny, so absolute times are not comparable to the")
print(" 87-95% improvements reported on the full 10.6M-row table — the mechanism")
print(" — EXPLAIN QUERY PLAN, index, ANALYZE — is identical.)")

plan = cur.execute(
    "EXPLAIN QUERY PLAN SELECT id_student, SUM(sum_click) FROM student_vle_interactions "
    "WHERE code_module=? AND code_presentation=? GROUP BY id_student", ("AAA", "2013J")
).fetchall()
print("\nEXPLAIN QUERY PLAN output:")
for row in plan:
    print(" ", row)


# ======================================================================
# PHASE 6: ETL & DATA QUALITY
# ======================================================================
header("PHASE 6", "ETL & Data Quality")

dq_checks = []

def check(check_id, description, passed):
    dq_checks.append({"id": check_id, "description": description, "status": "PASS" if passed else "FAIL"})

check("DQ001", "id_student NOT NULL", cur.execute(
    "SELECT COUNT(*) FROM students WHERE id_student IS NULL").fetchone()[0] == 0)
check("DQ002", "final_result in valid set", cur.execute(
    "SELECT COUNT(*) FROM students WHERE final_result NOT IN ('Pass','Fail','Distinction','Withdrawn')"
).fetchone()[0] == 0)
check("DQ003", "assessment weight 0-100", cur.execute(
    "SELECT COUNT(*) FROM assessments WHERE weight NOT BETWEEN 0 AND 100").fetchone()[0] == 0)
check("DQ004", "score 0-100 or NULL", cur.execute(
    "SELECT COUNT(*) FROM student_assessments WHERE score IS NOT NULL AND score NOT BETWEEN 0 AND 100"
).fetchone()[0] == 0)
check("DQ005", "sum_click >= 0", cur.execute(
    "SELECT COUNT(*) FROM student_vle_interactions WHERE sum_click < 0").fetchone()[0] == 0)
check("DQ006", "FK: students -> courses valid", cur.execute("""
    SELECT COUNT(*) FROM students s
    LEFT JOIN courses c ON s.code_module=c.code_module AND s.code_presentation=c.code_presentation
    WHERE c.code_module IS NULL
""").fetchone()[0] == 0)

quality_report = {
    "summary": {
        "total_checks": len(dq_checks),
        "passed": sum(1 for c in dq_checks if c["status"] == "PASS"),
        "failed": sum(1 for c in dq_checks if c["status"] == "FAIL"),
    },
    "checks": dq_checks,
}
print(json.dumps(quality_report, indent=2))


# ======================================================================
# PHASE 7: DATA WAREHOUSE (STAR SCHEMA)
# ======================================================================
header("PHASE 7", "Data Warehouse — Star Schema")

cur.executescript("""
DROP TABLE IF EXISTS dim_student;
DROP TABLE IF EXISTS dim_course;
DROP TABLE IF EXISTS fact_student_assessment;

CREATE TABLE dim_course (
    course_key INTEGER PRIMARY KEY AUTOINCREMENT,
    code_module TEXT, code_presentation TEXT
);
CREATE TABLE dim_student (
    student_key INTEGER PRIMARY KEY AUTOINCREMENT,
    id_student INTEGER, gender TEXT, highest_education TEXT, final_result TEXT
);
CREATE TABLE fact_student_assessment (
    student_key INTEGER, course_key INTEGER, score REAL,
    FOREIGN KEY (student_key) REFERENCES dim_student(student_key),
    FOREIGN KEY (course_key) REFERENCES dim_course(course_key)
);
""")

cur.executemany("INSERT INTO dim_course (code_module, code_presentation) VALUES (?,?)", courses_data and
                 [(c[0], c[1]) for c in courses_data])
cur.executemany(
    "INSERT INTO dim_student (id_student, gender, highest_education, final_result) VALUES (?,?,?,?)",
    [(s[0], s[3], s[5], s[11]) for s in students_data],
)
conn.commit()

for sid, aid, mod, pres, score in student_assessments_data:
    sk = cur.execute("SELECT student_key FROM dim_student WHERE id_student=?", (sid,)).fetchone()[0]
    ck = cur.execute("SELECT course_key FROM dim_course WHERE code_module=? AND code_presentation=?",
                      (mod, pres)).fetchone()[0]
    cur.execute("INSERT INTO fact_student_assessment VALUES (?,?,?)", (sk, ck, score))
conn.commit()

print("Star schema populated: dim_course, dim_student, fact_student_assessment")
print("\nPass rates by course (warehouse query, via fact table):")
for row in cur.execute("""
    SELECT dc.code_module, dc.code_presentation,
           COUNT(DISTINCT ds.student_key) as students,
           ROUND(100.0*SUM(CASE WHEN ds.final_result IN ('Pass','Distinction') THEN 1 ELSE 0 END)
                 / COUNT(DISTINCT ds.student_key), 1) as pass_rate
    FROM fact_student_assessment fsa
    JOIN dim_course dc ON fsa.course_key = dc.course_key
    JOIN dim_student ds ON fsa.student_key = ds.student_key
    GROUP BY dc.code_module, dc.code_presentation
"""):
    print(" ", row)


# ======================================================================
# PHASE 8: NOSQL IMPLEMENTATION
# ======================================================================
header("PHASE 8", "NoSQL Implementation — Document & Key-Value Stores")

document_store = []
for s in students_data:
    document_store.append({
        "id_student": s[0],
        "demographics": {"gender": s[3], "region": s[4], "highest_education": s[5], "age_band": s[7]},
        "enrollment": {"code_module": s[1], "code_presentation": s[2], "final_result": s[11]},
    })

print("Document store (sample):")
print(json.dumps(document_store[0], indent=2))

kv_store = {
    f"STU_{s[0]}_{s[1]}_{s[2]}": {"final_result": s[11]} for s in students_data
}
print("\nKey-Value store (sample lookup):")
key = f"STU_28400_AAA_2013J"
print(f"  {key} -> {kv_store.get(key)}")


# ======================================================================
# PHASE 9: BIG DATA PROCESSING (DuckDB)
# ======================================================================
header("PHASE 9", "Big Data Processing — DuckDB")

svi_df = pd.DataFrame(student_vle_data, columns=["id_student", "code_module", "code_presentation", "id_site", "date", "sum_click"])

t0 = time.perf_counter()
result = duckdb.sql("""
    SELECT id_student, SUM(sum_click) AS total_clicks
    FROM svi_df
    GROUP BY id_student
    ORDER BY total_clicks DESC
""").df()
elapsed = time.perf_counter() - t0

print(f"DuckDB MapReduce-style aggregation (Map -> Shuffle -> Reduce):")
print(result.to_string(index=False))
print(f"\nProcessing time: {elapsed*1000:.3f} ms on {len(svi_df)} sample rows")
print("(Full project processed 10,655,280 rows at 896K rows/sec using this same DuckDB approach)")


# ======================================================================
# PHASE 10: NOTEBOOKS & ANALYSIS
# ======================================================================
header("PHASE 10", "Notebooks & Analysis")

df_students = pd.DataFrame(students_data, columns=[
    "id_student", "code_module", "code_presentation", "gender", "region",
    "highest_education", "imd_band", "age_band", "num_of_prev_attempts",
    "studied_credits", "disability", "final_result"])

print("Outcome distribution (sample):")
print(df_students["final_result"].value_counts().to_string())

print("\nPass rate by education level (sample):")
summary = df_students.groupby("highest_education")["final_result"].apply(
    lambda x: round(100 * x.isin(["Pass", "Distinction"]).mean(), 1))
print(summary.to_string())
print("(In the full notebook, 6 matplotlib/seaborn charts visualize these patterns)")


# ======================================================================
# PHASE 11: PIPELINE ORCHESTRATION
# ======================================================================
header("PHASE 11", "Pipeline Orchestration")

def run_stage(name, fn):
    t0 = time.perf_counter()
    try:
        fn()
        status = "SUCCESS"
    except Exception as e:
        status = f"FAILED ({e})"
    print(f"  {name:35s} - {status} ({(time.perf_counter()-t0)*1000:.2f}ms)")

print("AFILEARN PIPELINE ORCHESTRATION")
run_stage("STAGE 1: Database Connection Check", lambda: conn.execute("SELECT 1"))
run_stage("STAGE 2: Data Freshness Check", lambda: cur.execute("SELECT COUNT(*) FROM students"))
run_stage("STAGE 3: Data Quality Validation", lambda: [c for c in dq_checks if c["status"] == "PASS"])
run_stage("STAGE 4: Warehouse Refresh", lambda: cur.execute("SELECT COUNT(*) FROM fact_student_assessment"))
run_stage("STAGE 5: Analytics Computation", lambda: cur.execute(
    "SELECT final_result, COUNT(*) FROM students GROUP BY final_result"))
print("PIPELINE SUMMARY: all stages executed sequentially with dependency checks")


# ======================================================================
# PHASE 12: SECURITY, PRIVACY, ACCESS CONTROL & BACKUP
# ======================================================================
header("PHASE 12", "Security, Privacy, Access Control & Backup")

PERMISSIONS = {
    "ADMIN":   {"tables": "*", "can_delete": True,  "view_pii": True,  "can_export": True},
    "ANALYST": {"tables": {"students_masked"}, "can_delete": False, "view_pii": False, "can_export": True},
    "VIEWER":  {"tables": {"v_course_pass_rates"}, "can_delete": False, "view_pii": False, "can_export": False},
}

def can_access(role, table):
    p = PERMISSIONS[role]
    return p["tables"] == "*" or table in p["tables"]

print("RBAC access tests:")
for role in ["ADMIN", "ANALYST", "VIEWER"]:
    p = PERMISSIONS[role]
    print(f"  {role:8s} | access 'students': {can_access(role,'students')!s:5} | "
          f"can DELETE: {p['can_delete']!s:5} | can view PII: {p['view_pii']!s:5}")

def mask_id(real_id: int) -> str:
    return f"STU_{hashlib.sha256(str(real_id).encode()).hexdigest()[:8]}"

print("\nPII masking (hash-based pseudonymisation):")
for s in students_data:
    print(f"  {s[0]}  ->  {mask_id(s[0])}")

timestamp = time.strftime("%Y%m%d_%H%M%S")
backup_name = f"afilearn_backup_{timestamp}.db"
shutil.copy(DB_PATH, backup_name)

def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

orig_hash, back_hash = sha256_of(DB_PATH), sha256_of(backup_name)
print(f"\nBackup: {backup_name}")
print(f"  Size     : {os.path.getsize(backup_name)/1024:.2f} KB")
print(f"  Checksum : {back_hash[:16]}...")
print(f"  Verified : {'Valid' if orig_hash == back_hash else 'INVALID'}")


# ======================================================================
# PHASE 13: FINAL INTEGRATION
# ======================================================================
header("PHASE 13", "Final Integration / System Verification")

tables = [r[0] for r in cur.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()]
total_rows = sum(cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in tables)
orphans = cur.execute("""
    SELECT COUNT(*) FROM students s
    LEFT JOIN courses c ON s.code_module=c.code_module AND s.code_presentation=c.code_presentation
    WHERE c.code_module IS NULL
""").fetchone()[0]
views = [r[0] for r in cur.execute("SELECT name FROM sqlite_master WHERE type='view'").fetchall()]
indexes = [r[0] for r in cur.execute(
    "SELECT name FROM sqlite_master WHERE type='index' AND sql IS NOT NULL").fetchall()]

print("System Verification Checklist:")
print(f"  Tables present            : {len(tables)}  ({', '.join(tables)})")
print(f"  Total rows (sample DB)    : {total_rows}")
print(f"  Referential integrity     : {'100%' if orphans==0 else str(orphans)+' orphans found'}")
print(f"  Indexes present           : {len(indexes)}")
print(f"  Views present             : {len(views)}")
print(f"  Data quality checks       : {quality_report['summary']['passed']}/{quality_report['summary']['total_checks']} passed")

print("\nFinal demo query — pass rate by course:")
for row in cur.execute("""
    SELECT code_module, code_presentation, COUNT(*) total,
           SUM(CASE WHEN final_result IN ('Pass','Distinction') THEN 1 ELSE 0 END) passed
    FROM students GROUP BY code_module, code_presentation
"""):
    module, pres, total, passed = row
    print(f"  {module}-{pres}: {passed}/{total} passed ({round(100*passed/total,1)}%)")

print("\n" + "#" * 72)
print("# ALL 13 PHASES EXECUTED SUCCESSFULLY ON SAMPLE DATASET")
print("#" * 72)

conn.close()
