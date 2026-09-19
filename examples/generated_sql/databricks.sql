-- UNEXECUTED INCOMPLETE SQL FRAGMENT (NOT EQUIVALENT TO THE GOVERNED PLAN): Databricks execution is disabled locally.
-- Use the governed plan, approved France mapping, and native Databricks security.
SELECT partner.partner_id, COUNT(DISTINCT posting.journal_entry_id) AS posting_count
FROM s4hana_france.business_partner.partners AS partner
JOIN s4hana_france.sales_order.orders AS ord
    ON partner.partner_id = ord.partner_id
JOIN s4hana_france.finance_acdoca.postings AS posting
    ON ord.sales_order_id = posting.sales_order_id
WHERE posting.posting_status IN (?, ?)
GROUP BY partner.partner_id;
