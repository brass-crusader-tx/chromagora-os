# Demo Factory v0.1 Acceptance Test

Successful Demo Factory v0.1 must allow:

1. Operator uploads the top-100 CSV.
2. Batch rows are created in Rank order.
3. Worker starts at row 1.
4. Worker crawls the business site.
5. Old-site screenshot is captured.
6. BrandDoc is generated.
7. Framework retrieval happens for conversion strategy.
8. Each agent stage calls OpenRouter separately or mock provider in dev/test.
9. SiteSpec is assembled.
10. Demo renders locally at `/demo/{slug}`.
11. Before/after reveal works on mobile.
12. Footer appears at bottom center with Chromagora C link.
13. Review section only includes verified reviews or is omitted.
14. Adversarial checker prevents fake trust claims.
15. Visual QA produces mobile and desktop screenshots.
16. Publish creates `{slug}.demo.chromagora.com` deployment record.
17. Batch continues to row 2 without manual intervention.
18. Rate limit causes cooldown, not terminal failure.
19. Failed row is marked retryable/terminal without killing whole batch.
20. Cockpit shows progress and demo links.

Explicitly not in v0.1:

| Not Included | Reason |
|---|---|
| Deploying to client-owned domains | Private demo subdomains are enough for outreach. |
| Sending outreach automatically | Operator review remains required. |
| Full CMS editing | Renderer-safe SiteSpec is the edit boundary. |
| Fully custom generated React per prospect | Deterministic rendering is a hard architecture rule. |
| Perfect stock-image sourcing | Neutral relevant stock can be acceptable; proof-implying images need stricter review. |
| Autonomous payment/client onboarding | Demo Factory ends at private demo production and cockpit review. |
