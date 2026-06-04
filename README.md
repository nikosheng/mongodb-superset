# MongoDB 8 + Apache Superset Demo

This project runs a demo stack with:

- MongoDB 8 (data source)
- Apache Superset (BI / visualization)
- PyMongoSQL inside Superset (MongoDB driver for Superset)

Superset connects to MongoDB using:

`mongodb://...?...&mode=superset`

## Prerequisites

- Docker and Docker Compose installed
- Available ports:
  - 27017 for MongoDB
  - 8088 for Superset

## Start the environment

The first run builds a custom Superset image with `pymongosql` preinstalled.

```bash
docker compose up -d --build
```

Check status:

```bash
docker compose ps
```

## Access

- Superset: `http://localhost:8088`
- MongoDB: `mongodb://root:example@localhost:27017`

Superset admin account:

- Username: `admin`
- Password: `admin`

## Seeded demo data

A seed container inserts demo records into the `demo` database with two collections:

### Collection: `sales`

Document schema:

```json
{
  "_id":        "ObjectId",
  "item":       "String",
  "category":   "String",
  "region":     "String",
  "amount":     "Number",
  "quantity":   "Number",
  "order_date": "Date"
}
```

Example document:

```json
{
  "_id":        "ObjectId('...')",
  "item":       "Laptop",
  "category":   "Electronics",
  "region":     "NA",
  "amount":     1299,
  "quantity":   3,
  "order_date": "2025-01-10T00:00:00Z"
}
```

### Collection: `players` (Casino Player Profiles)

25 fake casino player records demonstrating MongoDB's document model — each record contains a **profile subdocument**, a **contacts array**, and a **game_sessions array of subdocuments**.

Document schema:

```json
{
  "_id":               "ObjectId",
  "player_id":         "String",
  "name":              "String",
  "status":            "String (Active | Inactive | Banned)",
  "vip_tier":          "String (Bronze | Silver | Gold | Platinum)",
  "registration_date": "Date",
  "total_wagered":     "Number",
  "total_won":         "Number",
  "profile": {
    "age":                "Number",
    "gender":             "String",
    "preferred_language": "String",
    "address": {
      "street":  "String",
      "city":    "String",
      "country": "String (ISO 3166-1 alpha-2)"
    }
  },
  "contacts": [
    {
      "type":  "String (email | phone)",
      "value": "String"
    }
  ],
  "game_sessions": [
    {
      "game":       "String (Slots | Blackjack | Roulette | Baccarat | Poker)",
      "bet_amount": "Number",
      "outcome":    "String (win | loss)",
      "payout":     "Number",
      "played_at":  "Date"
    }
  ]
}
```

Example document:

```json
{
  "_id":               "ObjectId('...')",
  "player_id":         "PLR-001",
  "name":              "James Carter",
  "status":            "Active",
  "vip_tier":          "Platinum",
  "registration_date": "2021-03-15T00:00:00Z",
  "total_wagered":     85200,
  "total_won":         72400,
  "profile": {
    "age":                42,
    "gender":             "Male",
    "preferred_language": "English",
    "address": {
      "street":  "88 Lucky Ave",
      "city":    "Las Vegas",
      "country": "US"
    }
  },
  "contacts": [
    { "type": "email", "value": "jcarter@email.com" },
    { "type": "phone", "value": "+1-702-555-0101" }
  ],
  "game_sessions": [
    { "game": "Baccarat",  "bet_amount": 5000, "outcome": "win",  "payout": 9500, "played_at": "2025-05-01T20:00:00Z" },
    { "game": "Blackjack", "bet_amount": 2000, "outcome": "loss", "payout": 0,    "played_at": "2025-05-03T22:15:00Z" },
    { "game": "Roulette",  "bet_amount": 1500, "outcome": "win",  "payout": 5250, "played_at": "2025-05-10T19:30:00Z" },
    { "game": "Poker",     "bet_amount": 3000, "outcome": "win",  "payout": 7200, "played_at": "2025-05-18T21:00:00Z" }
  ]
}
```

### Collection: `casino_visits` (Physical Casino Visits)

30 visit records linked to the `players` collection via `player_id` — demonstrating a cross-collection relationship (the MongoDB equivalent of a foreign key).

Document schema:

```json
{
  "_id":                 "ObjectId",
  "visit_id":            "String",
  "player_id":           "String  ← foreign key → players.player_id",
  "casino_name":         "String",
  "city":                "String",
  "country":             "String (ISO 3166-1 alpha-2)",
  "check_in":            "Date",
  "check_out":           "Date",
  "table_games_played":  "Number",
  "slots_played":        "Number",
  "food_beverage_spend": "Number",
  "hotel_stay":          "Boolean",
  "host_assigned":       "String | null"
}
```

Example document:

```json
{
  "_id":                 "ObjectId('...')",
  "visit_id":            "VIS-001",
  "player_id":           "PLR-001",
  "casino_name":         "Bellagio",
  "city":                "Las Vegas",
  "country":             "US",
  "check_in":            "2025-01-15T18:00:00Z",
  "check_out":           "2025-01-15T23:30:00Z",
  "table_games_played":  3,
  "slots_played":        1,
  "food_beverage_spend": 120,
  "hotel_stay":          false,
  "host_assigned":       "Mike Torres"
}
```

## Casino Player demo queries

**Syntax rules:**
- The pipeline and options must be single-quoted JSON strings.
- `WHERE` on fields that exist in the `$project` output works correctly.
- `WHERE` filters are applied **after** the pipeline (Python-side post-filter). Push filters into a `$match` stage inside the pipeline for best performance.
- SQL-level `GROUP BY` on the result does **not** work — push `$group` into the pipeline instead.
- `LIMIT` works correctly.

**Example — filter sessions for one player:**

```sql
SELECT name, vip_tier, game, bet_amount
FROM players.aggregate(
  '[{"$unwind": "$game_sessions"},
    {"$project": {"name": "$name", "vip_tier": "$vip_tier",
                  "game": "$game_sessions.game",
                  "bet_amount": "$game_sessions.bet_amount"}}]',
  '{}'
)
WHERE name = 'James Carter'
```

**Example — filter by projected array field:**

```sql
SELECT name, game, bet_amount
FROM players.aggregate(
  '[{"$unwind": "$game_sessions"},
    {"$project": {"name": 1, "game": "$game_sessions.game",
                  "bet_amount": "$game_sessions.bet_amount",
                  "outcome": "$game_sessions.outcome"}}]',
  '{}'
)
WHERE game = 'Poker'
```

**Example — aggregation pushed into the pipeline (`$group` inside pipeline):**

```sql
SELECT game, total_sessions, total_bet
FROM players.aggregate(
  '[{"$unwind": "$game_sessions"},
    {"$group": {"_id": "$game_sessions.game",
                "total_sessions": {"$sum": 1},
                "total_bet":      {"$sum": "$game_sessions.bet_amount"}}},
    {"$project": {"game": "$_id", "total_sessions": 1, "total_bet": 1, "_id": 0}},
    {"$sort": {"total_bet": -1}}]',
  '{}'
)
```

### Query 1 — Player roster with profile subdocument fields

Subdocument fields are accessed with dot notation directly in SELECT:

```sql
SELECT player_id, name, vip_tier, status,
       "profile.age" AS age, "profile.gender" AS gender,
       "profile.address.city" AS city, "profile.address.country" AS country
FROM players
```

### Query 2 — All game sessions (one row per session)

Query the `player_sessions` view created in Step 1:

```sql
SELECT name, vip_tier, game, bet_amount, outcome, payout, played_at
FROM player_sessions
LIMIT 100
```

### Query 3 — Total wagered and won per VIP tier

```sql
SELECT vip_tier,
       SUM(total_wagered) AS total_wagered,
       SUM(total_won)     AS total_won
FROM players
GROUP BY vip_tier
ORDER BY total_wagered DESC
```

### Query 4 — Player count by status

```sql
SELECT status, COUNT(*) AS player_count
FROM players
GROUP BY status
ORDER BY player_count DESC
```

### Query 5 — Win/loss session count and total payout by game

Uses the `player_sessions` view:

```sql
SELECT game, outcome,
       COUNT(*)         AS session_count,
       SUM(bet_amount)  AS total_bet,
       SUM(payout)      AS total_payout
FROM player_sessions
GROUP BY game, outcome
ORDER BY game, outcome
```

### Query 6 — Player profile joined to casino visits (`$lookup` join)

Uses the `player_visits` view (players joined to casino_visits on `player_id`):

```sql
SELECT player_id, name, vip_tier, visit_id,
       casino_name, city, country,
       table_games_played, food_beverage_spend, hotel_stay, host_assigned
FROM player_visits
LIMIT 50
```

### Query 7 — Total visits and spend per player (aggregated join)

```sql
SELECT name, vip_tier,
       COUNT(*)                  AS total_visits,
       SUM(table_games_played)   AS total_table_games,
       SUM(food_beverage_spend)  AS total_fnb_spend
FROM player_visits
GROUP BY name, vip_tier
ORDER BY total_visits DESC
```

### Query 8 — Total F&B spend per country across all visits

```sql
SELECT country,
       COUNT(*)                  AS visit_count,
       SUM(food_beverage_spend)  AS total_fnb_spend
FROM player_visits
GROUP BY country
ORDER BY total_fnb_spend DESC
```

## Suggested Superset charts (players collection)

Create datasets from the `players` collection and the `player_sessions` view (after running Step 1 above).

| Chart type | Dataset | Setup |
|---|---|---|
| **Pie chart** | `players` | Dimension: `vip_tier` · Metric: `COUNT(*)` — VIP tier distribution |
| **Bar chart** | `players` | X-axis: `vip_tier` · Metrics: `SUM(total_wagered)`, `SUM(total_won)` — wagered vs won by tier |
| **Pie chart** | `players` | Dimension: `status` · Metric: `COUNT(*)` — player status breakdown |
| **Big Number** | `players` | Metric: `SUM(total_wagered)` — total lifetime wagers across all players |
| **Table** | `players` | Columns: `player_id`, `name`, `vip_tier`, `profile.address.city`, `profile.address.country`, `total_wagered` — player lookup |
| **Bar chart** | `player_sessions` | X-axis: `game` · Metric: `SUM(bet_amount)` — total bets by game type |
| **Bar chart** | `player_sessions` | X-axis: `game` · Breakout: `outcome` · Metric: `COUNT(*)` — win/loss ratio per game |
| **Line chart** | `player_sessions` | X-axis: `played_at` · Metric: `SUM(bet_amount)` — betting activity over time |
| **Bar chart** | `player_visits` | X-axis: `name` · Metric: `COUNT(*)` — visits per player |
| **Bar chart** | `player_visits` | X-axis: `country` · Metric: `SUM(food_beverage_spend)` — F&B spend by country |
| **Table** | `player_visits` | Columns: `name`, `vip_tier`, `casino_name`, `city`, `check_in`, `food_beverage_spend`, `hotel_stay` — visit log |
| **Pie chart** | `player_visits` | Dimension: `casino_name` · Metric: `COUNT(*)` — most visited casinos |

## Connect Superset to MongoDB

1. Open Superset: `http://localhost:8088`
2. Go to Settings -> Database Connections
3. Click + Database
4. Choose MongoDB (or Other if MongoDB is not listed)
5. Use this SQLAlchemy URI:

```text
mongodb://root:example@mongodb:27017/demo?authSource=admin&mode=superset
```

6. Click Test Connection
7. Click Connect

## Run your first query

In SQL Lab -> SQL Editor, choose the MongoDB connection and run:

```sql
SELECT item, category, region, amount, quantity
FROM sales
LIMIT 20
```

Aggregation example:

```sql
SELECT category, SUM(amount) AS total_amount, SUM(quantity) AS total_qty
FROM sales
GROUP BY category
ORDER BY total_amount DESC
```

## Create a chart

1. Run a query in SQL Lab
2. Click Explore (or Save -> Save dataset first if prompted)
3. Pick chart type (for example, Bar Chart)
4. Example setup:
   - X-axis: `category`
   - Metric: `SUM(amount)`
5. Click Run
6. Save chart and optionally add to a dashboard

## Stop and clean up

Stop containers:

```bash
docker compose down
```

Stop and remove volumes (deletes MongoDB and Superset persisted data):

```bash
docker compose down -v
```

## Troubleshooting

- If MongoDB connection fails, verify URI includes `authSource=admin` and `mode=superset`.
- If Superset is up but login/setup is not ready, wait about 30 seconds and refresh.
- If you updated `Dockerfile.superset`, rebuild and restart:

```bash
docker compose up -d --build
```
- Re-run startup from clean state if needed:

```bash
docker compose down -v
docker compose up -d --build
```
