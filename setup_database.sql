-- Snowflake Database Setup for Analytics POC
-- Run these commands in Snowflake to set up the database schema and sample data

-- Switch to the target database and create schema
USE DATABASE MAPS_SEARCH_ANALYTICS;
CREATE SCHEMA IF NOT EXISTS APPLICATION;
USE SCHEMA APPLICATION;

-- Create Users table
CREATE OR REPLACE TABLE USERS (
    user_id NUMBER AUTOINCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    full_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP(),
    updated_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Create Regions table
CREATE OR REPLACE TABLE REGIONS (
    region_id NUMBER PRIMARY KEY,
    region_name VARCHAR(100) NOT NULL,
    region_code VARCHAR(10) NOT NULL,
    country VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE
);

-- Create User Region Mapping table
CREATE OR REPLACE TABLE USER_REGION_MAPPING (
    mapping_id NUMBER AUTOINCREMENT PRIMARY KEY,
    user_id NUMBER NOT NULL,
    region_id NUMBER NOT NULL,
    access_level VARCHAR(20) DEFAULT 'read',
    granted_by NUMBER,
    granted_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP(),
    FOREIGN KEY (user_id) REFERENCES USERS(user_id),
    FOREIGN KEY (granted_by) REFERENCES USERS(user_id)
);

-- Create Sales Data table
CREATE OR REPLACE TABLE SALES_DATA (
    sale_id NUMBER AUTOINCREMENT PRIMARY KEY,
    customer_name VARCHAR(100) NOT NULL,
    region_id NUMBER NOT NULL,
    product_category VARCHAR(50),
    revenue NUMBER(12,2),
    quantity NUMBER(8,2),
    sale_date DATE,
    quarter VARCHAR(10),
    year NUMBER(4),
    sales_rep VARCHAR(100),
    created_at TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP()
);

-- Insert sample regions
INSERT INTO REGIONS (region_id, region_name, region_code, country) VALUES
(1, 'North America', 'NA', 'USA'),
(2, 'Europe', 'EU', 'Germany'),
(3, 'Asia Pacific', 'APAC', 'Singapore'),
(4, 'Latin America', 'LATAM', 'Brazil');

-- Insert sample users (password hash is for 'password123')
INSERT INTO USERS (username, password_hash, email, full_name) VALUES
('alice.smith', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeADBPOhRGN.8f6YG', 'alice@company.com', 'Alice Smith'),
('bob.jones', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeADBPOhRGN.8f6YG', 'bob@company.com', 'Bob Jones'),
('carol.wong', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeADBPOhRGN.8f6YG', 'carol@company.com', 'Carol Wong');

-- Insert user region assignments
INSERT INTO USER_REGION_MAPPING (user_id, region_id, access_level) VALUES
(1, 1, 'read'),  -- Alice can access North America
(1, 2, 'read'),  -- Alice can access Europe
(2, 1, 'read'),  -- Bob can access North America only
(3, 3, 'read'),  -- Carol can access Asia Pacific
(3, 4, 'read');  -- Carol can access Latin America

-- Insert sample sales data
INSERT INTO SALES_DATA (customer_name, region_id, product_category, revenue, quantity, sale_date, quarter, year, sales_rep) VALUES
-- North America data
('ABC Corp', 1, 'Software', 150000.00, 50, '2024-10-15', 'Q4 2024', 2024, 'John Doe'),
('XYZ Inc', 1, 'Hardware', 75000.00, 25, '2024-09-20', 'Q3 2024', 2024, 'Jane Smith'),
('TechStart LLC', 1, 'Software', 95000.00, 30, '2024-11-02', 'Q4 2024', 2024, 'John Doe'),
('DataCorp', 1, 'Services', 120000.00, 40, '2024-08-10', 'Q3 2024', 2024, 'Jane Smith'),

-- Europe data  
('European Ltd', 2, 'Software', 200000.00, 75, '2024-11-01', 'Q4 2024', 2024, 'Pierre Martin'),
('UK Solutions', 2, 'Services', 90000.00, 30, '2024-08-15', 'Q3 2024', 2024, 'Emma Wilson'),
('Germany Tech', 2, 'Hardware', 85000.00, 35, '2024-09-25', 'Q3 2024', 2024, 'Pierre Martin'),
('France Systems', 2, 'Software', 110000.00, 45, '2024-10-20', 'Q4 2024', 2024, 'Emma Wilson'),

-- Asia Pacific data
('APAC Systems', 3, 'Software', 125000.00, 40, '2024-10-30', 'Q4 2024', 2024, 'Hiroshi Tanaka'),
('Singapore Tech', 3, 'Hardware', 85000.00, 35, '2024-09-10', 'Q3 2024', 2024, 'Li Wei'),
('Tokyo Innovations', 3, 'Services', 95000.00, 25, '2024-11-12', 'Q4 2024', 2024, 'Hiroshi Tanaka'),
('Sydney Solutions', 3, 'Software', 80000.00, 30, '2024-08-28', 'Q3 2024', 2024, 'Li Wei'),

-- Latin America data
('Brazil Enterprises', 4, 'Software', 110000.00, 45, '2024-11-15', 'Q4 2024', 2024, 'Carlos Santos'),
('Mexico Solutions', 4, 'Services', 65000.00, 20, '2024-08-25', 'Q3 2024', 2024, 'Maria Rodriguez'),
('Argentina Tech', 4, 'Hardware', 70000.00, 25, '2024-09-18', 'Q3 2024', 2024, 'Carlos Santos'),
('Chile Systems', 4, 'Software', 88000.00, 35, '2024-10-05', 'Q4 2024', 2024, 'Maria Rodriguez');

-- Create function to get current user's accessible regions
CREATE OR REPLACE SECURE FUNCTION get_user_regions()
RETURNS ARRAY
LANGUAGE SQL
AS
$$
    SELECT ARRAY_AGG(region_id) 
    FROM USER_REGION_MAPPING 
    WHERE user_id = GETVARIABLE('CURRENT_USER_ID')::NUMBER
    AND access_level IN ('read', 'write', 'admin')
$$;

-- Create Row Access Policy for SALES_DATA
CREATE OR REPLACE ROW ACCESS POLICY sales_data_access_policy AS (region_id NUMBER) 
RETURNS BOOLEAN ->
    CASE
        -- Validate session context exists
        WHEN GETVARIABLE('CURRENT_USER_ID') IS NULL THEN FALSE
        -- Admin override for troubleshooting
        WHEN GETVARIABLE('IS_ADMIN')::BOOLEAN = TRUE THEN TRUE
        -- Check if region_id is in user's accessible regions
        WHEN ARRAY_CONTAINS(
            region_id::VARIANT, 
            PARSE_JSON(GETVARIABLE('ACCESSIBLE_REGIONS'))
        ) THEN TRUE
        -- Deny by default
        ELSE FALSE
    END;

-- Apply the policy to SALES_DATA table
ALTER TABLE SALES_DATA ADD ROW ACCESS POLICY sales_data_access_policy ON (region_id);

-- Create semantic view for Cortex Analyst
CREATE OR REPLACE SEMANTIC VIEW sales_analytics_semantic_view

  TABLES (
    sales_data AS MAPS_SEARCH_ANALYTICS.APPLICATION.SALES_DATA
      PRIMARY KEY (sale_id)
      COMMENT = 'Sales transaction data with regional segmentation',
    regions AS MAPS_SEARCH_ANALYTICS.APPLICATION.REGIONS
      PRIMARY KEY (region_id)
      COMMENT = 'Regional information for sales territories'
  )

  RELATIONSHIPS (
    sales_to_regions AS
      sales_data (region_id) REFERENCES regions
  )

--   FACTS (
--     sales_data.sale_count AS COUNT(sale_id)
--       COMMENT = 'Count of individual sales transactions'
--   )

  DIMENSIONS (
    sales_data.customer_name AS customer_name
      COMMENT = 'Name of the customer who made the purchase',
    sales_data.product_category AS product_category
      COMMENT = 'Category of product sold (Software, Hardware, Services)',
    sales_data.quarter AS quarter
      COMMENT = 'Business quarter of the sale (e.g., Q1 2024, Q2 2024)',
    sales_data.year AS year
      COMMENT = 'Year when the sale occurred',
    sales_data.sales_rep AS sales_rep
      COMMENT = 'Name of the sales representative',
    sales_data.sale_date AS sale_date
      COMMENT = 'Date when the sale was completed',
    regions.region_name AS region_name
      COMMENT = 'Full name of the sales region',
    regions.region_code AS region_code  
      COMMENT = 'Short code for the region (NA, EU, APAC, LATAM)',
    regions.country AS country
      COMMENT = 'Primary country for the region'
  )

  METRICS (
    sales_data.total_revenue AS SUM(revenue)
      COMMENT = 'Total revenue amount from sales in USD',
    sales_data.total_quantity AS SUM(quantity)
      COMMENT = 'Total number of units sold',
    sales_data.average_revenue AS AVG(revenue)
      COMMENT = 'Average revenue per sale',
    sales_data.sale_count AS COUNT(sale_id)
      COMMENT = 'Total number of sales transactions'
  )

  COMMENT = 'Sales data analytics semantic view for multi-region access with Cortex Analyst';

-- Grant access to the semantic view
GRANT SELECT ON SEMANTIC VIEW sales_analytics_semantic_view TO ROLE PUBLIC;
GRANT REFERENCES ON SEMANTIC VIEW sales_analytics_semantic_view TO ROLE PUBLIC;

-- Display setup completion message
SELECT 'Database setup completed successfully!' AS status,
       'Semantic view created: sales_analytics_semantic_view' AS semantic_view,
       'Ready for Cortex Analyst queries' AS next_step;
