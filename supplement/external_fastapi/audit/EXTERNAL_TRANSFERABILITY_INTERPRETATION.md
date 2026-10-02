# External transferability interpretation — R5

The external pilot uses four official FastAPI tutorial source files from repository commit
`33d411dbc3236275dd64d200bfe18d5d60a49b2e` and FastAPI 0.128.2 / Pydantic 2.13.4 to generate OpenAPI 3.1 publication artifacts.

R5 corrects the earlier query-role checker so source-declared role/name are evaluated explicitly rather than echoed only in explanatory text. For the constrained query example, `Query(alias="item-query")` establishes a source expectation of `query/item-query`; the generated OpenAPI parameter must match both fields. Deliberate mutations to `header` and `wrong-parameter` are rejected and are retained in `external_role_negative_controls.json`.

The four-obligation checklist is applied with explicit applicability gates:

1. **Source-role accuracy** compares source parameter/request-body roles and names with generated OpenAPI locations/names.
2. **Condition disclosure** compares source-declared validation constraints with generated schema constraints and checks runtime rejection of invalid values. This is an explicit adaptation because FastAPI publishes declarative validation metadata rather than arbitrary internal branch guards.
3. **Representation-disagreement preservation** returns **N/A** in all four examples because none contains an unresolved explicit conflict between coexisting representations.
4. **Review-authority consistency** returns **N/A** in all four examples because the examples do not carry a human review state. Two examples additionally exercise a **status-propagation analogue**: `deprecated=True` in source must propagate to OpenAPI `deprecated=true`. The analogue is not counted as a direct review-authority pass.

Direct checklist result after checker repair: **7 applicable checks, 7 passes, 0 failures, 9 N/A cells** across the 16 example-by-obligation cells. Two lifecycle-status analogue checks also pass. The two query-role negative controls fail as expected.

This pilot demonstrates bounded transfer of the source-role and declarative-condition procedures to an independently developed generator. It does not establish external defect prevalence, full four-obligation transfer, or population-level checker accuracy.
