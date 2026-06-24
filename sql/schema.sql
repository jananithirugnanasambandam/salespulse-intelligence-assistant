-- ── STEP 1: DROP TABLES IF THEY EXIST (safe reset) ──
DROP TABLE IF EXISTS Fact_Customer_Activity CASCADE;
DROP TABLE IF EXISTS Fact_Sales             CASCADE;
DROP TABLE IF EXISTS Dim_Budget_Targets     CASCADE;
DROP TABLE IF EXISTS Dim_Customer           CASCADE;
DROP TABLE IF EXISTS Dim_Store              CASCADE;
DROP TABLE IF EXISTS Dim_Product            CASCADE;
DROP TABLE IF EXISTS Dim_Date               CASCADE;
DROP TABLE IF EXISTS Data_Quality_Log       CASCADE;

-- ── TABLE 1: Dim_Date ────────────────────────────────
CREATE TABLE Dim_Date (
    date_id     SERIAL       PRIMARY KEY,
    full_date   DATE         NOT NULL UNIQUE,
    day         SMALLINT     NOT NULL,
    month       SMALLINT     NOT NULL,
    month_name  VARCHAR(20)  NOT NULL,
    quarter     SMALLINT     NOT NULL,
    year        SMALLINT     NOT NULL,
    is_ramadan  BOOLEAN      NOT NULL DEFAULT FALSE,
    is_weekend  BOOLEAN      NOT NULL DEFAULT FALSE
);

-- ── TABLE 2: Dim_Product ─────────────────────────────
CREATE TABLE Dim_Product (
    product_id    SERIAL        PRIMARY KEY,
    product_name  VARCHAR(150)  NOT NULL,
    category      VARCHAR(80)   NOT NULL,
    subcategory   VARCHAR(80)   NOT NULL,
    unit_price    DECIMAL(10,2) NOT NULL
);

-- ── TABLE 3: Dim_Store ───────────────────────────────
CREATE TABLE Dim_Store (
    store_id    SERIAL        PRIMARY KEY,
    store_name  VARCHAR(150)  NOT NULL,
    city        VARCHAR(50)   NOT NULL,
    region      VARCHAR(50)   NOT NULL,
    country     VARCHAR(50)   NOT NULL DEFAULT 'UAE'
);

-- ── TABLE 4: Dim_Customer ────────────────────────────
CREATE TABLE Dim_Customer (
    customer_id          SERIAL        PRIMARY KEY,
    customer_name        VARCHAR(150)  NOT NULL,
    segment              VARCHAR(30)   NOT NULL,
    acquisition_date     DATE          NOT NULL,
    acquisition_channel  VARCHAR(50)   NOT NULL,
    city                 VARCHAR(50)   NOT NULL,
    lifetime_value       DECIMAL(12,2) NOT NULL
);

-- ── TABLE 5: Dim_Budget_Targets ──────────────────────
CREATE TABLE Dim_Budget_Targets (
    budget_id       SERIAL        PRIMARY KEY,
    store_id        INT           NOT NULL,
    year            SMALLINT      NOT NULL,
    month           SMALLINT      NOT NULL,
    month_name      VARCHAR(20)   NOT NULL,
    revenue_target  DECIMAL(12,2) NOT NULL,
    profit_target   DECIMAL(12,2) NOT NULL
);

-- ── TABLE 6: Data_Quality_Log ────────────────────────
CREATE TABLE Data_Quality_Log (
    log_id      SERIAL        PRIMARY KEY,
    check_name  VARCHAR(150)  NOT NULL,
    result      INT           NOT NULL,
    status      VARCHAR(10)   NOT NULL,
    threshold   INT           NOT NULL DEFAULT 0,
    run_date    TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes       TEXT
);

-- ── TABLE 7: Fact_Sales ──────────────────────────────
CREATE TABLE Fact_Sales (
    sale_id     SERIAL        PRIMARY KEY,
    date_id     INT           NOT NULL REFERENCES Dim_Date(date_id),
    product_id  INT           NOT NULL REFERENCES Dim_Product(product_id),
    store_id    INT           NOT NULL REFERENCES Dim_Store(store_id),
    customer_id INT           NOT NULL REFERENCES Dim_Customer(customer_id),
    revenue     DECIMAL(12,2) NOT NULL,
    cost        DECIMAL(12,2) NOT NULL,
    profit      DECIMAL(12,2) NOT NULL,
    quantity    INT           NOT NULL,
    discount    DECIMAL(5,2)  NOT NULL DEFAULT 0,
    returns     SMALLINT      NOT NULL DEFAULT 0
);

-- ── TABLE 8: Fact_Customer_Activity ──────────────────
CREATE TABLE Fact_Customer_Activity (
    activity_id                 SERIAL        PRIMARY KEY,
    customer_id                 INT           NOT NULL REFERENCES Dim_Customer(customer_id),
    date_id                     INT           NOT NULL REFERENCES Dim_Date(date_id),
    last_purchase_date          DATE          NOT NULL,
    purchase_frequency          INT           NOT NULL,
    total_spend                 DECIMAL(12,2) NOT NULL,
    days_since_last_purchase    INT           NOT NULL,
    is_churned                  BOOLEAN       NOT NULL DEFAULT FALSE
);
