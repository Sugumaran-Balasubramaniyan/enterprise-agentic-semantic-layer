-- UNEXECUTED SIMULATION (INCOMPLETE SQL FRAGMENT; NOT EQUIVALENT TO THE GOVERNED PLAN): Microsoft Fabric execution is disabled locally.
-- Use the governed plan, approved Germany mapping, and native Fabric security.
SELECT partner.partner_id, COUNT(DISTINCT posting.journal_entry_id) AS posting_count
FROM dbo.partners AS partner
JOIN dbo.orders AS ord
    ON partner.partner_id = ord.partner_id
JOIN dbo.acdoca_postings AS posting
    ON ord.sales_order_id = posting.sales_order_id
WHERE posting.posting_status IN (?, ?)
GROUP BY partner.partner_id;
