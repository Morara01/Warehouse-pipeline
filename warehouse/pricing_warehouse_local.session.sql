DROP TABLE IF EXISTS fact_pricing_performance;
DROP TABLE IF EXISTS dim_product;
DROP TABLE IF EXISTS dim_region;


-- DIMENSION: REGION

CREATE TABLE IF NOT EXISTS dim_region (
    region_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    region_name VARCHAR(50) NOT NULL UNIQUE,
    target_revenue DECIMAL(12, 2),
    target_margin DECIMAL(5, 2)
) ENGINE=InnoDB;

-- DIMENSION: PRODUCT

CREATE TABLE IF NOT EXISTS dim_product (
    product_id INT UNSIGNED PRIMARY KEY,
    category VARCHAR(100),
    price_tier VARCHAR(50),
    brand_strength_score INT
) ENGINE=InnoDB;


-- FACT TABLE: PRICING PERFORMANCE

CREATE TABLE IF NOT EXISTS fact_pricing_performance (
    pricing_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

    product_id INT UNSIGNED NOT NULL,
    region_id INT UNSIGNED NOT NULL,

    base_cost DECIMAL(10, 2),
    recommended_selling_price DECIMAL(10, 2),
    mark_up_pct_used DECIMAL(5, 2),
    max_allowed_mark_uppct DECIMAL(5, 2),

    markup_compliant BOOLEAN,
    margin_vs_target DECIMAL(6, 2),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_product
        FOREIGN KEY (product_id)
        REFERENCES dim_product (product_id),

    CONSTRAINT fk_region
        FOREIGN KEY (region_id)
        REFERENCES dim_region (region_id)
) ENGINE=InnoDB;

SELECT * FROM dim_region;
SELECT * FROM dim_product;
SELECT COUNT(*) FROM fact_pricing_performance;