-- UNEXECUTED DOCUMENTATION EXAMPLE: Databricks execution is disabled locally.
-- Use the governed plan, approved France mapping, and native Databricks security.
SELECT customer.customer_id, COUNT(DISTINCT claim.claim_id) AS claim_count
FROM globalsure_france.insurance_customer.customers AS customer
JOIN globalsure_france.insurance_policy.policies AS policy
    ON customer.customer_id = policy.customer_id
JOIN globalsure_france.insurance_claim.claims AS claim
    ON policy.policy_id = claim.policy_id
WHERE claim.status IN (?, ?, ?)
GROUP BY customer.customer_id;
