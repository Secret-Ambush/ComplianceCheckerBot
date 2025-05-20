# 📋 Compliance Report

## 📎 Matched Documents:
- **Invoice**: `tmpbhlj38ml.PDF`

---

## ✅❌ Rule Evaluation Summary:
### ❌ FAIL – `RULE_INV_DATE_CURR_001`
- **Result**: FAIL
- **Reason**: Invoice date is not in January or invoice currency is not AED
- **LLM Insight**: The rule failed because the invoice date is not in the month of January as required. The extracted invoice date is '12-Aug-2023', which is in the month of August, not January. Additionally, there is no information provided about the invoice currency, which should be in AED as per the rule.

To fix this, ensure that the invoice date is within the month of January and the currency used is AED. If the invoice date or currency is incorrect, you may need to issue a new invoice with the correct details. If the extraction is incorrect, you may need to re-scan the document or manually input the correct details.


---

## 📊 Summary:
- Total rules evaluated: **1**
- ✅ Passed: **0**
- ❌ Failed: **1**
- ⚠️ Rules with missing inputs: RULE_INV_DATE_CURR_001