# Crypto Trading Web App

## Overview

This repository contains a self–hosted web application for visualising and
analysing cryptocurrency spot markets on Binance.  It provides a simple
web interface built with HTML, CSS and vanilla JavaScript for viewing
candlestick charts, calculating technical indicators (exponential moving
averages and RSI), fetching basic trading recommendations and
evaluating your portfolio balance.  The backend is implemented using
[FastAPI](https://fastapi.tiangolo.com/) and is split into a number of
focused routers and services to keep the logic easy to reason about and
test.

The application does **not** execute trades on your behalf.  Endpoints
that would place orders are intentionally omitted from the current
version.  Instead it focuses on market data retrieval, indicator
visualisation and portfolio valuation.  See the deprecated
`oldapp.py` for a historical reference that included order preview and
confirmation logic.

## Features

* **Interactive charts** – Powered by
  [TradingView Lightweight Charts](https://www.tradingview.com/lightweight-charts/)
  to display candlesticks and RSI, with optional overlays for EMA‑12
  and EMA‑26.
* **Real‑time updates** – Once a chart is loaded the client subscribes
  to Binance WebSocket streams to update the most recent candle as new
  trades occur.
* **Technical indicators** – Both client and server compute EMAs and
  RSI so that indicators are available even if the WebSocket stream
  lags behind.
* **Trading recommendations** – A very simple signal derived from
  crossover of EMA‑12 and EMA‑26 with RSI filtering.  Signals are
  categorised as `BUY`, `SELL` or `HOLD`.
* **Portfolio valuation** – Fetch your account balances from Binance
  (when API keys are configured) and estimate the total value in USDT
  using a lightweight price cache.
* **Modular architecture** – Application logic is organised into
  dedicated routers and service modules making it easy to extend and
  unit test.

## Getting Started

### Prerequisites

* Python 3.10 or later.
* A Binance account.  API keys are optional but required to use the
  portfolio endpoint.

### Installation

Clone this repository and install the dependencies into a virtual
environment:

```bash
git clone https://github.com/Valik1314/crypto-trading.git
cd crypto-trading
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Create a `.env` file in the project root (the same directory as
`requirements.txt`) and set your Binance API credentials if you wish to
enable authenticated endpoints:

```bash
BINANCE_API_KEY=your_api_key
BINANCE_API_SECRET=your_api_secret
# optional – override the base URL to use the testnet
USE_TESTNET=1
```

If you omit the API key and secret the application will still run, but
endpoints that require authentication (such as `/api/portfolio/valued`)
will return an error.

### Running the Application

Launch the FastAPI app using `uvicorn`:

```bash
uvicorn app.main:app --reload
```

By default the server listens on `127.0.0.1:8000`.  Navigate to
`http://127.0.0.1:8000` in your browser to load the frontend.  You can
interactively change the trading pair and time frame, toggle indicators
and fetch trading recommendations.  Clicking **Портфель** will display
your portfolio valuation (only if API keys are configured).

### Running Tests

Basic unit and integration tests are included under the `tests/`
directory.  The test suite is written using Python's built‑in
`unittest` framework so no third‑party testing dependencies are
required.  To execute the tests, run:

```bash
python -m unittest discover -s tests -v
```

The tests use FastAPI's `TestClient` along with `unittest.mock` to
avoid making real network calls.  They cover the EMA/RSI indicator
logic, cache behaviour and API endpoints.

## Contributing

Contributions to improve the UI, extend functionality or fix bugs are
welcome.  Please fork the repository, create a feature branch and open
a pull request with a clear description of your changes.

## License

This project is provided "as‑is" without any warranty.  The code is
licensed under the MIT License.
