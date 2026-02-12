<div align="center">
  <h1>tech-calendar</h1>
  <h4 align="center">
    Subscribe-ready ICS feeds for earnings.
  </h4>
  <p>Earnings dates published as ICS feeds you can subscribe to.</p>
</div>

> [!WARNING]
> This calendar is for planning purposes only. Do not use it for trading or investment decisions.

## ✨ What this is

A calendar with **quarterly earnings dates of popular tech companies** with a horizon of the next 20 days

### 📊 Companies included

| Company            | Symbol |
|--------------------|--------|
| Alphabet (Google)  | GOOGL  |
| Amazon             | AMZN   |
| Apple              | AAPL   |
| Meta               | META   |
| Microsoft          | MSFT   |
| Netflix            | NFLX   |
| NVIDIA             | NVDA   |

### 📝 Example event

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

## 📥 Subscribe

## 📥 Add this calendar

> [!TIP]
> Subscribing with the link below keeps the calendar **updated automatically**, no re-imports needed. You can unsubscribe at any time.

👉 Copy this link:
```
https://raw.githubusercontent.com/eikendev/tech-calendar/refs/heads/public/calendar.ics
```

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
  api_key: <your API key>  # or set TC_FINNHUB_API_KEY environment
  days_ahead: 20
  days_past: 10
```

## 🏃 Run this tool

Run the earnings workflow:

```bash
tech-calendar earnings
```
