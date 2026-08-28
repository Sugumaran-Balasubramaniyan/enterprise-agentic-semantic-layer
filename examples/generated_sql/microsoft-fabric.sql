-- UNEXECUTED DOCUMENTATION EXAMPLE: Microsoft Fabric execution is disabled locally.
-- Use the governed plan, approved Germany mapping, and native Fabric security.
SELECT customer.customer_id, COUNT(DISTINCT claim.claim_id) AS claim_count
FROM dbo.customers AS customer
JOIN dbo.policies AS policy
    ON customer.customer_id = policy.customer_id
JOIN dbo.claims AS claim
    ON policy.policy_id = claim.policy_id
WHERE claim.status IN (?, ?, ?)
GROUP BY customer.customer_id;
