-- UNEXECUTED SIMULATION (INCOMPLETE SQL FRAGMENT; NOT EQUIVALENT TO THE GOVERNED PLAN): Snowflake execution is disabled locally.
-- Use the governed plan, approved United Kingdom mapping, and native Snowflake security.
SELECT partner.partner_id, COUNT(DISTINCT posting.journal_entry_id) AS posting_count
FROM S4HANA_UK.BP.PARTNERS AS partner
JOIN S4HANA_UK.SALES.ORDERS AS ord
    ON partner.partner_id = ord.partner_id
JOIN S4HANA_UK.FINANCE.POSTINGS AS posting
    ON ord.sales_order_id = posting.sales_order_id
WHERE posting.posting_status IN (?, ?)
GROUP BY partner.partner_id;
