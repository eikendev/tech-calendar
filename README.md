<div align="center">
  <h1>tech-calendar</h1>
  <h4 align="center">
    Subscribe-ready ICS feeds for earnings and tech events.
  </h4>
  <p>Earnings dates and annual tech events, published as ICS feeds you can subscribe to.</p>
</div>

> [!WARNING]
> This calendar is for planning purposes only. Do not use it for trading or investment decisions.

## ✨ What this is

A calendar with
- **quartlery earnings dates of popular tech companies** with a horizon of the next 20 days
- annual **tech event calendar** (developer conferences) populated by an AI researcher

### 📊 Companies included (earnings)

| Company            | Symbol |
|--------------------|--------|
| Alphabet (Google)  | GOOGL  |
| Amazon             | AMZN   |
| Apple              | AAPL   |
| Meta               | META   |
| Microsoft          | MSFT   |
| Netflix            | NFLX   |
| NVIDIA             | NVDA   |

### 📝 Example event (earnings)

**Event name**
```
NVDA Q2 Earnings
```

**Event details**
```
Ticker: NVDA
Fiscal Qtr: 2
Estimate EPS: 1.0281
Est. Revenue: 46.98 B
Source: Finnhub
```

## 📥 Subscribe to these calendars

- Earnings feed: `public/earnings.ics`
- Events feed: `public/events.ics`

Most calendar apps refresh subscribed ICS URLs automatically; no re-imports needed.

### Apple Calendar (Mac / iPhone / iPad)
- Mac: Calendar → File → New Calendar Subscription… → paste the ICS URL.
- iPhone/iPad: Settings → Calendar → Accounts → Add Account → Other → Add Subscribed Calendar → paste the ICS URL.

### Google Calendar
- Open Google Calendar.
- Left sidebar → Other calendars → From URL → paste the ICS URL → Add calendar.

### Outlook
- Open Outlook.
- File → Account Settings → Internet Calendars → New… → paste the ICS URL → confirm.

## 🚀 Install this tool

Install tech-calendar using `uv`:

```bash
uv tool install tech-calendar
```

Install tech-calendar using `pip`:

```bash
pip install tech-calendar
```

## ⚙️ Configure this tool

Create a configuration file at `~/.config/tech-calendar/config.yaml`:

```yaml
storage:
  db_path: "tech_calendar.db"

earnings:
  calendar:
    ics_path: "earnings.ics"
    relcalid: "tech.calendar.earnings"
    name: "Tech Earnings Calendar"
    description: "Earnings dates for selected tickers."
    retention_years: 5
  tickers: ["AAPL", "MSFT", "GOOG"]
  api_key: <your API key>  # or set FINNHUB_API_KEY environment
  days_ahead: 20
  days_past: 10

events:
  calendar:
    ics_path: "events.ics"
    relcalid: "tech.calendar.events"
    name: "Tech Event Calendar"
    description: "Annual technology events."
    retention_years: 5
  series:
    - id: "google-io"
      name: "Google I/O"
      queries: ["Google I/O", "Google developer conference"]
    - id: "apple-wwdc"
      name: "Apple WWDC"
      queries: ["Apple WWDC", "Worldwide Developers Conference Apple"]
```

## 🏃 Run this tool

Run the earnings workflow:

```bash
tech-calendar earnings
```

Run the events workflow:

```bash
tech-calendar events
```
