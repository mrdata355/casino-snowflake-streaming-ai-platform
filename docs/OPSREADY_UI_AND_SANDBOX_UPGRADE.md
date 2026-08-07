# OpsReady UI integrity + live sandbox upgrade

## What was fixed

A real V6 interaction bug was identified: the original renderer created the same element IDs (`code`, `run`, `resetCode`, `out`, `reason`, `fb`) in all three platform workspaces. Global `getElementById` lookups could therefore bind a Databricks or SQL Server action to the first Snowflake element. V6 now uses a scoped renderer (`v6-engine-v2.js`) with per-workspace class selectors and explicit listeners.

## Engineer View controls

The UI integrity layer covers the role switch, sidebar navigation, dashboard jump actions, weekly/monthly/FinOps graders, Incident → Training generator, Production Control Room selectors, full-screen simulator launch, score capture, modal close, and Simulation Library launch controls.

V6 additionally marks and wires platform task selectors, simulation grading, reset, real-sandbox execution, tab navigation, gateway test, session cleanup, and progress reset.

## Manager View controls

Manager View now includes functional actions rather than static cards only:

- assign the recommended drill to the team
- assign a drill to an individual demo engineer
- refresh captured evidence
- export evidence to CSV
- clear browser-only evidence
- run the UI Self-Test

The UI Self-Test checks duplicate IDs, navigation targets, jump targets, required primary controls, Production Control Room configuration, simulator-card rendering, unregistered visible controls, and availability of major simulator HTML assets.

## Certification controls

Certification now has explicit evidence actions. The demo can recalculate Senior Resilience and Staff/Principal status from recorded attempts and successful live-sandbox tasks. These are OpsReady demonstration thresholds, not an external credential.

## Live execution boundary

`services/sandbox_gateway` provides a server-side FastAPI gateway for eligible V6 tasks. Cloud/database credentials are never stored in browser localStorage. The browser only stores the gateway URL and short-lived session IDs.

The default profile is schema-safe. Broad account-level operations stay simulated unless a dedicated disposable training account/workspace explicitly enables admin labs. SQL Server can run as a local disposable container/database through the Compose `sandbox` profile. Snowflake and Databricks require deliberately configured training credentials on the gateway.

The public Vercel frontend must use an HTTPS gateway for live execution; an HTTPS page cannot call an HTTP localhost gateway because browsers block mixed content.
