# Part 2 — Governed Data Layer (Design Note)

Today the bot would get account data by scraping other microservices' logs — brittle and
ungoverned. This note replaces that with **two lanes**:

- **Lane 1 — Live data** (below): real-time reads (Balance, Card status, KYC, Transactions) via a
  governed API gateway.
- **Lane 2 — Batch data** (further down): behavioural analytics & historical data via an
  Airbyte → BigQuery medallion warehouse.

Diagram: `SadaDost-architecture.drawio.png` ([editable draw.io](https://drive.google.com/file/d/1tUdgqHjtqxiuZKh_S_5W7uEgwXhrajfz/view?usp=sharing)).

---

## Lane 1 — Live Data Lane

> How SadaDost fetches **live** customer data (Balance, Card status, KYC, Transactions)
> — replacing brittle, ungoverned log-scraping with governed REST APIs behind one gateway.

---

## The flow in one picture (words)

```
Customer → SadaDost → API Gateway / Aggregator → 4 owning microservices → one JSON back
```

SadaDost makes **exactly one call** to the gateway with a JWT. The gateway does all the work
(decode token → fan out → stitch) and hands back a single clean payload.

---

## Step by step

1. **Auth issues the token.** The Auth service generates a UUID per user (committed to the `users`
   DB) and issues a **signed JWT**. The UUID is the one shared id used across all services.

2. **SadaDost calls one endpoint.** SadaDost sends a single request —
   `GET /user-profile` with the **JWT in the Authorization header** (never a raw UUID in the URL).

3. **Gateway decodes the JWT.** The gateway decodes the token once, extracts the secure `user_id`
   (UUID), and injects it into every backend call. The customer id can't be tampered with or
   swapped, so the bot can't read customer B while logged in as A.

4. **Parallel fan-out.** The gateway calls all four services **at the same time**
   (`asyncio.gather`) with a short timeout, so total latency = the slowest single service, not the
   sum of all four.

   | Service       | Port  | Owns                  |
   |---------------|-------|-----------------------|
   | KYC           | 8081  | identity / KYC status |
   | Balance       | 8082  | account balance       |
   | Cards         | 8083  | card status           |
   | Transactions  | 8084  | recent transactions   |

5. **Each service filters its own fields.** Restricted fields (e.g. CNIC, PAN) are stripped
   **inside each microservice** — they never leave the service, so they never reach the gateway or
   the bot.

6. **Stitch + tiered failure handling.** The gateway merges the responses into one clean JSON:
   - **KYC / Balance = critical** → if they fail or time out, return an error.
   - **Cards / Transactions = non-critical** → on timeout, catch it, return `[]`/empty for that
     field, and still serve the rest. One broken service degrades gracefully instead of crashing
     the whole answer.

7. **Single payload back.** SadaDost gets one aggregated payload and answers the customer.

---

## The six required positions

**1. Who owns what data & how it's exposed**
Each microservice owns its domain — Balance, Cards, KYC, Transactions are the single source of
truth for their data, each fronted by its own REST API. Nothing is exposed directly; everything
goes through the API Gateway/Aggregator, the only thing SadaDost talks to. SadaDost never touches a
service or database directly.

**2. Never read the wrong customer's data / a forbidden field**
SadaDost sends a JWT, not a raw UUID. The gateway decodes it, extracts the secure `user_id`, and
injects that into every backend call — so the id can't be swapped or tampered with. Each service
returns only its allowed fields; forbidden fields (CNIC/PAN) are never in the response, so they
never reach the bot.

**3. Service slow or down mid-answer**
The gateway calls all services in parallel with a short timeout, so total latency = slowest single
service. Tiered failure: Balance/KYC critical → error if they fail; Cards/Transactions
non-critical → return `[]` on timeout and still serve the rest. Graceful degradation, not a crash.

**4. Data residency (financial data)**
Financial data stays inside its owning service and is read **live** through the gateway — never
copied out to an external store on the live path.

**5. Adding a new data signal later**
Additive, no rewrite: stand up the new service's REST API → add one more parallel call in the
aggregator → expose it in the stitched JSON. SadaDost keeps calling the same single gateway
endpoint.

**6. Scaling as services & AI use-cases multiply**
SadaDost talks only to the gateway, and each service scales independently behind it. New AI
use-cases reuse the same one aggregated endpoint instead of re-integrating four services. The
chokepoint to watch is the gateway itself — that's where caching, rate-limiting, and horizontal
scaling go as load grows.

---

## Trade-offs & deliberately deferred

- **Gateway is a single chokepoint** — accepted on purpose (one place for auth, field policy,
  audit). Mitigate with caching + horizontal scaling; deferred until load demands it.
- **Tiering is a judgment call** — Balance/KYC as hard-fail vs per-field degrade can be revisited
  per use-case.
- **No service mesh / circuit breaker** yet — deferred; the timeout + tiered fallback is enough at
  this scale.

---
---

## Lane 2 — Batch Data Lane

> For **non-real-time** signals — behavioural analytics and historical data — moved into a
> warehouse and served read-only. (Live financial reads stay in the Live Data Lane above.)

---

## The flow in one picture (words)

```
Sources → Airbyte (ELT) → BigQuery: bronze → silver → gold → FastAPI → SadaDost → User
```

Raw data is pulled out of each owning source by Airbyte, landed in a **medallion** warehouse
(bronze → silver → gold), and exposed only through a serving API. SadaDost never touches storage
directly — it just calls endpoints.

---

## Step by step

1. **Sources.** Product analytics (**PostHog / Mixpanel**), financial (**SadaPay**), KYC
   (**Persona**) — each owns its raw data.

2. **Ingestion (ELT).** All sources connect to **Airbyte** via connectors. If Airbyte has no
   connector for a source, we write a custom one.

3. **Bronze layer.** Airbyte dumps raw data into the **bronze** layer in **BigQuery** (landing
   zone — raw, untransformed).

4. **Silver layer.** **Airflow** DAGs transform bronze → **silver**: cleaned data, via stored
   procedures (plus features extracted through ML models / statistical methods where needed).

5. **Gold layer.** Silver → **gold**: business-ready, read-only, aggregated tables.

6. **Segregation.** Data is split by type — events, profile, account, etc. — each in its own
   tables, populated by the stored procedures above.

7. **Serving.** **FastAPI** endpoints read from the silver/gold layers and serve the frontend and
   AI/ML services: `API → SadaDost → User`.

---

## The six required positions

**1. Who owns what data & how it's exposed**
Source services own the raw data. It flows through Airbyte (via connectors) from each owning source
into the BigQuery bronze layer, and is exposed **only through the serving API**. SadaDost never owns
or touches storage directly — it just calls endpoints.

**2. Never read the wrong customer's data / a forbidden field**
Every request carries a token scoped to one customer, so the system can't return customer B's data
to customer A. Forbidden fields never cross from bronze → silver (or are encrypted if they must be
kept).

**3. Service slow or down mid-answer**
The data API client uses a long timeout with basic-auth HTTP calls; if a downstream call fails,
that task degrades/errors while the rest of the pipeline continues — but there's **no automatic
failover**, so a hard outage means a partial or failed answer. (Honest limitation.)

**4. Data residency (financial data)**
Financial data lives in BigQuery and is accessible via the API.

**5. Adding a new data signal later**
Add the source to the ingestion via a DAG → expose a new data endpoint → register it in SadaDost's
ENDPOINTS map. Each layer is pluggable, so it's additive, not a rewrite.

**6. Scaling as services & AI use-cases multiply**
Because SadaDost talks only to the API (not databases), and DAGs/endpoints are added independently
per signal, each layer scales separately — but the single data-repository API is the shared
chokepoint to watch as load grows.

---

## Why Airbyte (tooling choice)

- **Open-source** → no vendor lock-in, self-hostable (matters for **data residency** of financial
  data — keep it in your own cloud/region).
- **350+ pre-built connectors** (Stripe, PostHog, etc.) → don't build/maintain pipes yourself.
- **Cost** → free/self-hosted vs Fivetran's volume-based pricing that scales painfully.
- **Extensible** → custom connectors via CDK when a source isn't covered.
- **Alternatives:** Fivetran (managed but lock-in + cost), Stitch (simpler, fewer connectors),
  Meltano (OSS, Singer-based). Airflow is the *orchestrator*, not a mover — complementary.

**Trade-off:** Airbyte is batch/sync → data is a stale **copy**. Acceptable for analytics, **not**
for "what's my balance right now" — that must hit the owning service live (Live Data Lane).

---

## Live vs Batch — when each lane is used

| | **Live lane** | **Batch lane** |
|---|---|---|
| **Data** | Balance, card status, KYC, transactions | Behavioural analytics, historical/aggregated |
| **Freshness** | Real-time (read on demand) | Stale copy (synced on a schedule) |
| **Path** | Gateway → owning service APIs | Airbyte → BigQuery medallion → serving API |
| **Use for** | "What's my balance right now?" | "What products does this user engage with?" |
