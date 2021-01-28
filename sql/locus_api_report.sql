CREATE TABLE IF NOT EXISTS locus_api_report(
    "date" DATE,
    "whitelabel" INT,
    "customer" INT,
    "endpoint" TEXT,
    "total_counts" INT,
    PRIMARY KEY ("date", "whitelabel", "customer", "endpoint")
);
