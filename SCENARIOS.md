# Test Scenarios

## Mock GitHub issue

- **Issue ID:** QA-001
- **Title:** `[RFQA] Verify add/remove cart functionality`
- **State:** `Ready for QA`
- **User story:** As a shopper, I want to add a product to my cart and remove it so I can manage items before checkout.
- **Target:** SauceDemo public testing application

## Acceptance criteria

| ID | Acceptance criterion | Verification |
|---|---|---|
| AC1 | A shopper can add an available product to the cart. | Cart contains exactly one item after adding. |
| AC2 | The cart displays the selected product name and price. | Cart values match values captured from the product card before interaction. |
| AC3 | The cart badge reflects one item after adding one product. | Badge text equals `1`. |
| AC4 | Removing the selected product empties the cart and clears the badge. | Cart item count is zero and badge is absent. |
| AC5 | Results are evidence-based, not invented by the LLM. | Every result contains an observed value and an evidence path; the final report is generated from structured checks. |

## Execution scenario

1. Open the target application.
2. Log in with the public SauceDemo demo account.
3. Capture the first product's name and price before interacting.
4. Provide the current UI inventory to the agent.
5. Ask the agent to add the first product and open the cart.
6. Verify AC1, AC2, and AC3 using Playwright.
7. Remove the product if exactly one cart item and a Remove button are present.
8. Verify AC4.
9. Generate the evidence-based final report and run status.

## Expected result

All functional criteria pass only when the live browser state proves them. If setup or navigation prevents a check, report a clear blocker/failure instead of assuming success.
