-- Template: substitute actual catalog and existing account groups before execution.
-- Restrict USE CATALOG / USE SCHEMA separately; create groups outside this project.
GRANT USE CATALOG ON CATALOG creditflow TO `creditflow_analysts`;
GRANT USE SCHEMA ON SCHEMA creditflow.demo TO `creditflow_analysts`;
GRANT SELECT ON VIEW creditflow.demo.gold_daily TO `creditflow_analysts`;
-- No SELECT grant on bronze/silver or features for the aggregate consumer.
-- Engineers and service principals receive narrowly scoped grants via administrator review.
