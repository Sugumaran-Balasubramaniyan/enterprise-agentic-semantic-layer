-- UNEXECUTED DOCUMENTATION EXAMPLE: Snowflake execution is disabled locally.
-- Use the governed plan, approved United Kingdom mapping, and native Snowflake security.
SELECT customer.customer_id, COUNT(DISTINCT claim.claim_id) AS claim_count
FROM GLOBALSURE_UK.CUSTOMER.CUSTOMERS AS customer
JOIN GLOBALSURE_UK.POLICY.POLICIES AS policy
    ON customer.customer_id = policy.customer_id
JOIN GLOBALSURE_UK.CLAIMS.CLAIMS AS claim
    ON policy.policy_id = claim.policy_id
WHERE claim.status IN (?, ?, ?)
GROUP BY customer.customer_id;
