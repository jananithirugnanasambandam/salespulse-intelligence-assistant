# ============================================================
#  SALES PULSE — Python ETL Pipeline
#  CSV → Staging → PostgreSQL (Star Schema)
#
#  What this script does:
#    1. Connects to PostgreSQL using SQLAlchemy
#    2. Reads all 7 CSV files using pandas
#    3. Cleans column names (lowercase, no spaces)
#    4. Casts every column to the correct data type
#    5. Validates data before loading
#    6. Creates staging tables first (raw copy)
#    7. Loads into final star schema tables
#    8. Logs all results to Data_Quality_Log
#    9. Prints a full summary report
#
#  Run:  python salespulse_etl.py
# ============================================================

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import logging
import time
import os
from datetime import datetime

# ── CONFIGURATION ────────────────────────────────────────
# Change these to match your PostgreSQL setup
DB_CONFIG = {
    "host":     "localhost",
    "port":     5432,
    "database": "salespulse",
    "user":     "postgres",
    "password": "Murugansaibaba",   
}

# Folder where your CSV files are saved
# Windows example: r"C:\Users\YourName\salespulse_data"
# Mac/Linux:       "/home/yourname/salespulse_data"
CSV_FOLDER = r"C:\SalesPulse Intelligence\data"

# ── LOGGING SETUP ────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.FileHandler("etl_log.txt"),   # saves to file
        logging.StreamHandler()                # prints to console
    ]
)
log = logging.getLogger(__name__)


# ============================================================
#  STEP 1 — DATABASE CONNECTION
# ============================================================

def get_engine():
    """
    Creates and returns a SQLAlchemy engine.
    Tests the connection before returning.
    """
    connection_string = (
        f"postgresql+psycopg2://"
        f"{DB_CONFIG['user']}:{DB_CONFIG['password']}"
        f"@{DB_CONFIG['host']}:{DB_CONFIG['port']}"
        f"/{DB_CONFIG['database']}"
    )
    try:
        engine = create_engine(
            connection_string,
            pool_pre_ping=True,     # checks connection is alive
            pool_size=5,            # max 5 connections in pool
            echo=False              # set True to see all SQL
        )
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        log.info("✅ Connected to PostgreSQL: salespulse database")
        return engine
    except SQLAlchemyError as e:
        log.error(f"❌ Database connection failed: {e}")
        log.error("Check: Is PostgreSQL running? Is password correct?")
        raise


# ============================================================
#  STEP 2 — COLUMN NAME CLEANER
# ============================================================

def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans all column names:
      - Converts to lowercase
      - Replaces spaces and hyphens with underscores
      - Removes special characters
      - Strips leading/trailing whitespace
    """
    original_cols = list(df.columns)
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(r"[\s\-]+", "_", regex=True)
        .str.replace(r"[^\w]",   "",  regex=True)
    )
    new_cols = list(df.columns)

    changed = [(o, n) for o, n in zip(original_cols, new_cols) if o != n]
    if changed:
        for old, new in changed:
            log.info(f"   Column renamed: '{old}' → '{new}'")

    return df


# ============================================================
#  STEP 3 — DATA TYPE CASTERS (one per table)
# ============================================================

def cast_dim_date(df: pd.DataFrame) -> pd.DataFrame:
    """Cast Dim_Date columns to correct types"""
    df["date_id"]    = df["date_id"].astype(np.int32)
    df["full_date"]  = pd.to_datetime(df["full_date"], format="%Y-%m-%d")
    df["day"]        = df["day"].astype(np.int8)
    df["month"]      = df["month"].astype(np.int8)
    df["month_name"] = df["month_name"].astype(str).str.strip()
    df["quarter"]    = df["quarter"].astype(np.int8)
    df["year"]       = df["year"].astype(np.int16)
    df["is_ramadan"] = df["is_ramadan"].astype(bool)
    df["is_weekend"] = df["is_weekend"].astype(bool)
    return df


def cast_dim_product(df: pd.DataFrame) -> pd.DataFrame:
    """Cast Dim_Product columns to correct types"""
    df["product_id"]   = df["product_id"].astype(np.int32)
    df["product_name"] = df["product_name"].astype(str).str.strip()
    df["category"]     = df["category"].astype(str).str.strip()
    df["subcategory"]  = df["subcategory"].astype(str).str.strip()
    df["unit_price"]   = pd.to_numeric(df["unit_price"], errors="coerce").round(2)
    return df


def cast_dim_store(df: pd.DataFrame) -> pd.DataFrame:
    """Cast Dim_Store columns to correct types"""
    df["store_id"]   = df["store_id"].astype(np.int32)
    df["store_name"] = df["store_name"].astype(str).str.strip()
    df["city"]       = df["city"].astype(str).str.strip()
    df["region"]     = df["region"].astype(str).str.strip()
    df["country"]    = df["country"].astype(str).str.strip()
    return df


def cast_dim_customer(df: pd.DataFrame) -> pd.DataFrame:
    """Cast Dim_Customer columns to correct types"""
    df["customer_id"]          = df["customer_id"].astype(np.int32)
    df["customer_name"]        = df["customer_name"].astype(str).str.strip()
    df["segment"]              = df["segment"].astype(str).str.strip()
    df["acquisition_date"]     = pd.to_datetime(df["acquisition_date"], format="%Y-%m-%d")
    df["acquisition_channel"]  = df["acquisition_channel"].astype(str).str.strip()
    df["city"]                 = df["city"].astype(str).str.strip()
    df["lifetime_value"]       = pd.to_numeric(df["lifetime_value"], errors="coerce").round(2)
    return df


def cast_dim_budget(df: pd.DataFrame) -> pd.DataFrame:
    """Cast Dim_Budget_Targets columns to correct types"""
    df["budget_id"]       = df["budget_id"].astype(np.int32)
    df["store_id"]        = df["store_id"].astype(np.int32)
    df["year"]            = df["year"].astype(np.int16)
    df["month"]           = df["month"].astype(np.int8)
    df["month_name"]      = df["month_name"].astype(str).str.strip()
    df["revenue_target"]  = pd.to_numeric(df["revenue_target"], errors="coerce").round(2)
    df["profit_target"]   = pd.to_numeric(df["profit_target"],  errors="coerce").round(2)
    return df


def cast_fact_sales(df: pd.DataFrame) -> pd.DataFrame:
    """Cast Fact_Sales columns to correct types"""
    df["sale_id"]     = df["sale_id"].astype(np.int32)
    df["date_id"]     = df["date_id"].astype(np.int32)
    df["product_id"]  = df["product_id"].astype(np.int32)
    df["store_id"]    = df["store_id"].astype(np.int32)
    df["customer_id"] = df["customer_id"].astype(np.int32)
    df["revenue"]     = pd.to_numeric(df["revenue"],  errors="coerce").round(2)
    df["cost"]        = pd.to_numeric(df["cost"],     errors="coerce").round(2)
    df["profit"]      = pd.to_numeric(df["profit"],   errors="coerce").round(2)
    df["quantity"]    = df["quantity"].astype(np.int16)
    df["discount"]    = pd.to_numeric(df["discount"], errors="coerce").round(4)
    df["returns"]     = df["returns"].astype(np.int8)
    return df


def cast_fact_activity(df: pd.DataFrame) -> pd.DataFrame:
    """Cast Fact_Customer_Activity columns to correct types"""
    df["activity_id"]                = df["activity_id"].astype(np.int32)
    df["customer_id"]                = df["customer_id"].astype(np.int32)
    df["date_id"]                    = df["date_id"].astype(np.int32)
    df["last_purchase_date"]         = pd.to_datetime(df["last_purchase_date"], format="%Y-%m-%d")
    df["purchase_frequency"]         = df["purchase_frequency"].astype(np.int16)
    df["total_spend"]                = pd.to_numeric(df["total_spend"], errors="coerce").round(2)
    df["days_since_last_purchase"]   = df["days_since_last_purchase"].astype(np.int16)
    df["is_churned"]                 = df["is_churned"].astype(bool)
    return df


# ============================================================
#  STEP 4 — DATA VALIDATOR
# ============================================================

def validate_dataframe(df: pd.DataFrame, table_name: str) -> dict:
    """
    Runs validation checks on a dataframe before loading.
    Returns a dict of check results.
    """
    results = {}

    # Check 1: No rows
    results["has_rows"] = len(df) > 0

    # Check 2: Null counts per column
    null_counts = df.isnull().sum()
    results["null_counts"] = null_counts[null_counts > 0].to_dict()
    results["has_nulls"]   = bool(null_counts.any())

    # Check 3: Duplicate primary key
    pk_col = f"{table_name.lower().replace('dim_','').replace('fact_','')}_id"
    if pk_col in df.columns:
        dupes = df[pk_col].duplicated().sum()
        results["duplicate_pks"] = int(dupes)
        results["has_duplicates"] = dupes > 0
    else:
        results["duplicate_pks"] = 0
        results["has_duplicates"] = False

    # Table-specific checks
    if table_name == "Fact_Sales":
        results["negative_revenue"] = int((df["revenue"] < 0).sum())
        results["zero_quantity"]    = int((df["quantity"] <= 0).sum())
        results["invalid_discount"] = int(
            ((df["discount"] < 0) | (df["discount"] > 1)).sum()
        )
        results["cost_gt_revenue"]  = int((df["cost"] > df["revenue"]).sum())

    if table_name == "Dim_Customer":
        valid_segments = {"VIP", "Regular", "At-Risk"}
        results["invalid_segments"] = int(
            ~df["segment"].isin(valid_segments).sum()
        )

    if table_name == "Dim_Date":
        results["future_dates"] = int(
            (df["full_date"] > pd.Timestamp.today()).sum()
        )

    return results


def print_validation_report(table_name: str, results: dict, row_count: int):
    """Prints a clean validation report for one table"""
    issues = []
    if not results["has_rows"]:
        issues.append("No rows loaded")
    if results["has_nulls"]:
        issues.append(f"Nulls found: {results['null_counts']}")
    if results["has_duplicates"]:
        issues.append(f"Duplicate PKs: {results['duplicate_pks']}")
    if results.get("negative_revenue", 0) > 0:
        issues.append(f"Negative revenue: {results['negative_revenue']} rows")
    if results.get("zero_quantity", 0) > 0:
        issues.append(f"Zero quantity: {results['zero_quantity']} rows")
    if results.get("invalid_discount", 0) > 0:
        issues.append(f"Invalid discount: {results['invalid_discount']} rows")
    if results.get("cost_gt_revenue", 0) > 0:
        issues.append(f"Cost > Revenue: {results['cost_gt_revenue']} rows")
    if results.get("future_dates", 0) > 0:
        issues.append(f"Future dates: {results['future_dates']} rows")

    status = "✅ PASS" if not issues else "⚠️  WARN"
    log.info(f"   {status}  {table_name:<30} {row_count:>6} rows")
    for issue in issues:
        log.warning(f"         └─ {issue}")


# ============================================================
#  STEP 5 — STAGING TABLE LOADER
# ============================================================

def load_to_staging(df: pd.DataFrame,
                    table_name: str,
                    engine) -> int:
    """
    Loads a dataframe into a staging table.
    Staging table name = stg_{table_name}
    Always drops and recreates — fresh load every run.
    Returns row count loaded.
    """
    staging_name = f"stg_{table_name.lower()}"

    try:
        # Convert datetime cols to string for staging
        # (staging is a raw copy — no type enforcement)
        df_stg = df.copy()
        for col in df_stg.select_dtypes(include=["datetime64[ns]"]).columns:
            df_stg[col] = df_stg[col].astype(str)

        df_stg.to_sql(
            name       = staging_name,
            con        = engine,
            if_exists  = "replace",   # drops and recreates
            index      = False,
            chunksize  = 1000,        # loads in 1000-row batches
            method     = "multi"      # faster multi-row inserts
        )
        log.info(f"   📦 Staging: {staging_name:<35} {len(df_stg):>6} rows loaded")
        return len(df_stg)

    except SQLAlchemyError as e:
        log.error(f"   ❌ Staging load failed for {staging_name}: {e}")
        raise


# ============================================================
#  STEP 6 — FINAL TABLE LOADER
# ============================================================

def load_to_final(df: pd.DataFrame,
                  table_name: str,
                  engine,
                  if_exists: str = "append") -> int:
    """
    Loads a dataframe into the final PostgreSQL table.
    if_exists options:
      'append'  → adds rows to existing table (default)
      'replace' → drops and recreates table (use with caution)
      'fail'    → raises error if table exists
    Returns row count loaded.
    """
    try:
        df.to_sql(
            name       = table_name.lower(),
            con        = engine,
            if_exists  = if_exists,
            index      = False,
            chunksize  = 1000,
            method     = "multi"
        )
        log.info(f"   ✅ Final:   {table_name.lower():<35} {len(df):>6} rows loaded")
        return len(df)

    except SQLAlchemyError as e:
        log.error(f"   ❌ Final load failed for {table_name}: {e}")
        raise


# ============================================================
#  STEP 7 — QUALITY LOG WRITER
# ============================================================

def log_quality_check(engine,
                      check_name: str,
                      result: int,
                      status: str,
                      notes: str = ""):
    """Writes one data quality result to Data_Quality_Log table"""
    sql = text("""
        INSERT INTO data_quality_log
            (check_name, result, status, threshold, run_date, notes)
        VALUES
            (:check_name, :result, :status, :threshold, :run_date, :notes)
    """)
    try:
        with engine.begin() as conn:
            conn.execute(sql, {
                "check_name": check_name,
                "result":     result,
                "status":     status,
                "threshold":  0,
                "run_date":   datetime.now(),
                "notes":      notes
            })
    except SQLAlchemyError as e:
        log.warning(f"   Could not write to quality log: {e}")


def run_quality_checks(engine):
    """
    Runs all 10 SQL quality checks against loaded data.
    Logs every result to Data_Quality_Log.
    """
    log.info("\n── Data Quality Checks ─────────────────────────────")

    checks = [
        {
            "name":  "Null Revenue Check",
            "sql":   "SELECT COUNT(*) FROM fact_sales WHERE revenue IS NULL",
            "pass":  0,
            "notes": "Revenue must never be NULL"
        },
        {
            "name":  "Duplicate Sale ID Check",
            "sql":   "SELECT COUNT(*) - COUNT(DISTINCT sale_id) FROM fact_sales",
            "pass":  0,
            "notes": "Every sale_id must be unique"
        },
        {
            "name":  "Negative Revenue Check",
            "sql":   "SELECT COUNT(*) FROM fact_sales WHERE revenue < 0",
            "pass":  0,
            "notes": "Revenue must be >= 0"
        },
        {
            "name":  "Future Date Check",
            "sql":   "SELECT COUNT(*) FROM dim_date WHERE full_date > CURRENT_DATE",
            "pass":  0,
            "notes": "No future dates in date dimension"
        },
        {
            "name":  "Orphaned Product Check",
            "sql":   """
                SELECT COUNT(*) FROM fact_sales f
                LEFT JOIN dim_product p ON f.product_id = p.product_id
                WHERE p.product_id IS NULL
            """,
            "pass":  0,
            "notes": "Every sale must link to a valid product"
        },
        {
            "name":  "Cost vs Revenue Check",
            "sql":   "SELECT COUNT(*) FROM fact_sales WHERE cost > revenue",
            "pass":  0,
            "notes": "Cost should not exceed revenue"
        },
        {
            "name":  "Discount Range Check",
            "sql":   "SELECT COUNT(*) FROM fact_sales WHERE discount < 0 OR discount > 1",
            "pass":  0,
            "notes": "Discount must be between 0.00 and 1.00"
        },
        {
            "name":  "Null Customer Check",
            "sql":   "SELECT COUNT(*) FROM fact_sales WHERE customer_id IS NULL",
            "pass":  0,
            "notes": "Every sale must have a customer"
        },
        {
            "name":  "Category Completeness Check",
            "sql":   "SELECT COUNT(*) FROM dim_product WHERE category IS NULL OR subcategory IS NULL",
            "pass":  0,
            "notes": "Every product must have category and subcategory"
        },
        {
            "name":  "Zero Quantity Check",
            "sql":   "SELECT COUNT(*) FROM fact_sales WHERE quantity <= 0",
            "pass":  0,
            "notes": "Quantity must be at least 1"
        },
    ]

    all_passed = True
    with engine.connect() as conn:
        for check in checks:
            result = conn.execute(text(check["sql"])).scalar()
            passed = result == check["pass"]
            status = "PASS" if passed else "FAIL"
            icon   = "✅" if passed else "❌"
            if not passed:
                all_passed = False

            log.info(f"   {icon} {check['name']:<40} result={result}  {status}")
            log_quality_check(
                engine,
                check["name"],
                result,
                status,
                check["notes"]
            )

    return all_passed


# ============================================================
#  STEP 8 — ROW COUNT VERIFIER
# ============================================================

def verify_row_counts(engine) -> dict:
    """
    Queries actual row counts from all loaded tables.
    Returns dict of {table_name: row_count}.
    """
    tables = [
        "dim_date", "dim_product", "dim_store",
        "dim_customer", "dim_budget_targets",
        "fact_sales", "fact_customer_activity",
        "data_quality_log"
    ]
    counts = {}
    with engine.connect() as conn:
        for t in tables:
            try:
                count = conn.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar()
                counts[t] = count
            except:
                counts[t] = "TABLE NOT FOUND"
    return counts


# ============================================================
#  MAIN ETL PIPELINE
# ============================================================

def run_etl():
    """
    Master function — runs the complete ETL pipeline.
    Order: Dimension tables first, then Fact tables.
    (Fact tables have foreign keys to dimension tables)
    """
    start_time = time.time()
    log.info("=" * 60)
    log.info("  SALES PULSE ETL PIPELINE — STARTING")
    log.info(f"  Run timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.info("=" * 60)

    # ── Connect ──────────────────────────────────────────
    log.info("\n── Step 1: Connecting to PostgreSQL ────────────────")
    engine = get_engine()

    # ── Table load config ────────────────────────────────
    # Order matters — dimension tables before fact tables
    TABLE_CONFIG = [
        {
            "csv":        "Dim_Date.csv",
            "table":      "Dim_Date",
            "cast_fn":    cast_dim_date,
            "type":       "dimension",
        },
        {
            "csv":        "Dim_Product.csv",
            "table":      "Dim_Product",
            "cast_fn":    cast_dim_product,
            "type":       "dimension",
        },
        {
            "csv":        "Dim_Store.csv",
            "table":      "Dim_Store",
            "cast_fn":    cast_dim_store,
            "type":       "dimension",
        },
        {
            "csv":        "Dim_Customer.csv",
            "table":      "Dim_Customer",
            "cast_fn":    cast_dim_customer,
            "type":       "dimension",
        },
        {
            "csv":        "Dim_Budget_Targets.csv",
            "table":      "Dim_Budget_Targets",
            "cast_fn":    cast_dim_budget,
            "type":       "dimension",
        },
        {
            "csv":        "Fact_Sales.csv",
            "table":      "Fact_Sales",
            "cast_fn":    cast_fact_sales,
            "type":       "fact",
        },
        {
            "csv":        "Fact_Customer_Activity.csv",
            "table":      "Fact_Customer_Activity",
            "cast_fn":    cast_fact_activity,
            "type":       "fact",
        },
    ]

    # ── ETL Loop ─────────────────────────────────────────
    log.info("\n── Step 2: Loading dimension tables ────────────────")

    summary = []
    errors  = []

    for cfg in TABLE_CONFIG:

        # Print section header for fact tables
        if cfg["type"] == "fact" and cfg == next(
            c for c in TABLE_CONFIG if c["type"] == "fact"
        ):
            log.info("\n── Step 3: Loading fact tables ─────────────────────")

        table_start = time.time()
        csv_path    = os.path.join(CSV_FOLDER, cfg["csv"])
        table_name  = cfg["table"]

        try:
            log.info(f"\n  📂 Processing: {table_name}")

            # ── 1. Read CSV ──────────────────────────────
            if not os.path.exists(csv_path):
                raise FileNotFoundError(
                    f"CSV not found: {csv_path}\n"
                    f"Check CSV_FOLDER setting at top of script."
                )
            df = pd.read_csv(csv_path, low_memory=False)
            log.info(f"   📄 Read:       {len(df):>6} rows  {len(df.columns)} columns")

            # ── 2. Clean column names ────────────────────
            df = clean_column_names(df)

            # ── 3. Cast data types ───────────────────────
            df = cfg["cast_fn"](df)
            log.info(f"   🔧 Cast:       data types applied")

            # ── 4. Validate ──────────────────────────────
            validation = validate_dataframe(df, table_name)
            print_validation_report(table_name, validation, len(df))

            # ── 5. Load to staging ───────────────────────
            load_to_staging(df, table_name, engine)

            # ── 6. Load to final table ───────────────────
            load_to_final(
                df,
                table_name,
                engine,
                if_exists="replace"   # safe for fresh load
            )

            elapsed = time.time() - table_start
            summary.append({
                "table":   table_name,
                "rows":    len(df),
                "status":  "SUCCESS",
                "time_s":  round(elapsed, 2)
            })

        except FileNotFoundError as e:
            log.error(f"   ❌ File error: {e}")
            errors.append({"table": table_name, "error": str(e)})

        except SQLAlchemyError as e:
            log.error(f"   ❌ Database error on {table_name}: {e}")
            errors.append({"table": table_name, "error": str(e)})

        except Exception as e:
            log.error(f"   ❌ Unexpected error on {table_name}: {e}")
            errors.append({"table": table_name, "error": str(e)})

    # ── Run Quality Checks ───────────────────────────────
    log.info("\n── Step 4: Running data quality checks ─────────────")
    if not errors:
        try:
            all_passed = run_quality_checks(engine)
        except Exception as e:
            log.warning(f"   Quality checks skipped: {e}")
            all_passed = False
    else:
        log.warning("   Quality checks skipped — errors during load")
        all_passed = False

    # ── Verify Row Counts ────────────────────────────────
    log.info("\n── Step 5: Verifying row counts ─────────────────────")
    counts = verify_row_counts(engine)
    expected = {
        "dim_date":               1096,
        "dim_product":              30,
        "dim_store":                10,
        "dim_customer":             50,
        "dim_budget_targets":      360,
        "fact_sales":            10000,
        "fact_customer_activity":  491,
    }
    all_counts_ok = True
    for table, expected_count in expected.items():
        actual = counts.get(table, 0)
        match  = "✅" if actual == expected_count else "⚠️ "
        if actual != expected_count:
            all_counts_ok = False
        log.info(
            f"   {match} {table:<35} "
            f"expected={expected_count:>5}  actual={actual:>5}"
        )

    # ── Final Summary ────────────────────────────────────
    total_time   = time.time() - start_time
    total_rows   = sum(s["rows"] for s in summary)
    success_tbls = len([s for s in summary if s["status"] == "SUCCESS"])
    failed_tbls  = len(errors)

    log.info("\n" + "=" * 60)
    log.info("  ETL PIPELINE COMPLETE")
    log.info("=" * 60)
    log.info(f"  Tables loaded:   {success_tbls} of {len(TABLE_CONFIG)}")
    log.info(f"  Total rows:      {total_rows:,}")
    log.info(f"  Quality checks:  {'ALL PASSED ✅' if all_passed else 'ISSUES FOUND ⚠️'}")
    log.info(f"  Row counts:      {'VERIFIED ✅' if all_counts_ok else 'MISMATCH ⚠️'}")
    log.info(f"  Time taken:      {total_time:.1f} seconds")

    if errors:
        log.info(f"\n  ❌ Failed tables ({failed_tbls}):")
        for err in errors:
            log.info(f"     • {err['table']}: {err['error'][:80]}")

    log.info("\n  Per-table summary:")
    log.info(f"  {'Table':<30} {'Rows':>6}  {'Time':>6}  Status")
    log.info(f"  {'-'*30} {'-'*6}  {'-'*6}  ------")
    for s in summary:
        log.info(
            f"  {s['table']:<30} {s['rows']:>6}  "
            f"{s['time_s']:>5.1f}s  {s['status']}"
        )

    if success_tbls == len(TABLE_CONFIG) and all_passed:
        log.info("\n  🎉 All done! Open Power BI and connect to salespulse database.")
        log.info("     Get Data → PostgreSQL → localhost → salespulse")
    else:
        log.info("\n  ⚠️  Pipeline completed with issues. Check log above.")

    log.info("=" * 60)
    engine.dispose()
    return len(errors) == 0


# ============================================================
#  ENTRY POINT
# ============================================================

if __name__ == "__main__":
    success = run_etl()
    exit(0 if success else 1)