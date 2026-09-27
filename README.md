# PricePing

A lightweight Python price tracker for Myntra.

PricePing lets you save Myntra product URLs and automatically check their prices once a day. When a product's price changes, PricePing sends an email notification.

## Features

* Track multiple Myntra products
* Automatically fetch the current product price
* Detect price increases and decreases
* Persist product state using Upstash Redis
* Send price-change notifications using Resend
* Remove products from the tracker
* Run daily using Windows Task Scheduler
* Simple CLI — no frontend or server required

## Architecture

```text
Windows Task Scheduler
        |
        v
python priceping.py --check-all
        |
        v
      Myntra
        |
        v
 Compare with previous price
        |
        v
   Upstash Redis
        |
        v
   Price changed?
      /     \
    No       Yes
    |         |
   Done     Resend
               |
               v
             Email
```

## Tech Stack

* **Python**
* **Requests** — HTTP requests
* **BeautifulSoup** — HTML parsing
* **Upstash Redis** — persistent product/price state
* **Resend** — email notifications
* **python-dotenv** — environment variable management
* **Windows Task Scheduler** — daily execution

## Project Structure

```text
PricePing/
├── priceping.py
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

`.env` is intentionally excluded from Git.

## Setup

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd PricePing
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root.
Copy `.env.example` to `.env` and replace the placeholder values with your actual credentials.

```env
RESEND_API_KEY=your_resend_api_key
EMAIL_TO=your_email@example.com

UPSTASH_REDIS_REST_URL=your_upstash_redis_url
UPSTASH_REDIS_REST_TOKEN=your_upstash_redis_token
```

## Usage

### Check a single product

```bash
python priceping.py <myntra-product-url>
```

For example:

```bash
python priceping.py https://www.myntra.com/...
```

The first check stores the product's current price.

Subsequent checks compare the current price with the previously stored price.

### Check all tracked products

```bash
python priceping.py --check-all
```

This loads all previously tracked products from Upstash Redis and checks each one.

### Remove a product

To stop tracking a specific product:

```bash
python priceping.py --remove "<myntra-product-url>"
```

The product is removed from the tracked products stored in Upstash Redis.

The removal operation does not make a request to Myntra.

## Price Change Notifications

When a price changes, PricePing sends an email containing:

* Product name
* Previous price
* Current price
* Amount of the change
* Link to the Myntra product

Both price decreases and increases are detected.

## Persistence

PricePing uses **Upstash Redis** to store the latest known state.

The stored data is conceptually:

```json
{
  "product-url": {
    "product_name": "Example Product",
    "price": 4999
  }
}
```

This means the application does not need a local `state.json` file and the tracked products persist across executions.

## Windows Task Scheduler Setup

PricePing can be scheduled to run automatically once a day using Windows Task Scheduler.

### 1. Open Task Scheduler

Search for **Task Scheduler** in Windows and open it.

Select:

**Task Scheduler Library → Create Basic Task**

### 2. Create the task

Use a name such as:

```text
PricePing Daily Check
```

Choose **Daily** as the trigger and select the time at which you want PricePing to run.

### 3. Configure the action

Select **Start a program**.

For **Program/script**, select the Python executable from the project's virtual environment:

```text
<project-directory>\.venv\Scripts\python.exe
```

For **Add arguments**, enter:

```text
<project-directory>\priceping.py --check-all
```

For **Start in**, enter:

```text
<project-directory>
```

Replace `<project-directory>` with the location where you cloned the repository.

### 4. Verify the task

After creating the task:

1. Open **Task Scheduler Library**.
2. Find `PricePing Daily Check`.
3. Right-click it and select **Run**.
4. Check **Last Run Result** after execution.

A successful run should report:

```text
0x0
```

### 5. Environment variables

Make sure the `.env` file exists in the project root and contains the required configuration:

```env
RESEND_API_KEY=your_resend_api_key
EMAIL_TO=your_email@example.com

UPSTASH_REDIS_REST_URL=your_upstash_redis_url
UPSTASH_REDIS_REST_TOKEN=your_upstash_redis_token
```

The `.env` file should **not** be committed to Git.

### Notes

* The computer must be running for the scheduled task to execute.
* The task should use the project's virtual environment so that all required dependencies are available.
* The **Start in** directory should point to the project root so that `.env` can be loaded correctly.


## Why Not GitHub Actions?

GitHub Actions was initially considered for daily scheduling.

However, Myntra returned a `200 OK` response containing a **Site Maintenance** page when requests were made from GitHub-hosted runners, while the same scraper worked normally from the local machine.

Therefore, daily execution is handled locally using Windows Task Scheduler instead of relying on GitHub-hosted runners.

GitHub is used as the source-code repository, while the actual scraper runs from the user's machine.

## Security

The following files should never be committed:

```text
.env
.venv/
__pycache__/
```

API keys and other credentials are supplied through environment variables.

## Limitations

* Currently supports **Myntra only**
* Designed for personal use
* Requires the computer to be available for the scheduled task
* Depends on Myntra's HTML structure and availability
* Uses a simple daily polling model
* No frontend or user authentication

## Future Ideas

If the project is expanded in the future, possible additions include:

* Support for additional sites
* Price history
* Configurable check intervals
* Price-drop thresholds
* Multiple notification channels
* A small web interface

These are intentionally outside the scope of the current MVP.

## License

This project is for personal/learning use.
