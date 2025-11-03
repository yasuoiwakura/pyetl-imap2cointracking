# pyetl-imap2cointracking-csv

Parse IMAP inbox and look for (german!!) DEGUSSA DCA Emails, generate csv file for Cointrackiing import

# pyetl-imap2cointracking-csv

Automated ETL from Degussa DCA emails to CoinTracking-compatible CSV.

## ⚡ Overview

This Python script connects to your email via IMAP, searches for Degussa DCA (Dollar-Cost Averaging) transactional emails, extracts the relevant gold investment data, and outputs it as a CoinTracking-compatible CSV file.

It is designed for investors and BI enthusiasts who want a quick way to track the performance of their Degussa Gold DCA without manually entering each micro-transaction.

## 📈 Problem (Investor Perspective)

1. Degussa offers a DCA where you typically
2. set up a standing order and send them, for example,
3. a monthly payment. They buy gold the day they receive your money and 
4. email you a confirmation including:

- Amount in €
- Gold price
- Gold amount purchased
- Total gold accumulated

5. When your savings target is reached, you can either collect the metal or (recommended)
6. deposit it in Degussa's custody.

## tax perspective (germany) NO COUNSELING HERE!
technically, for tax purposes, you "obtain" a coin or bullion only when you physically retrieve it. The accumulation over months/years doesn’t count for taxes.

## problem
From an investor perspective, however, you might want to track the performance of your DCA:
- How much did the €10 I invested last January grow?
- What is my ROI?

Manually importing these small transactions into CoinTracking every month is tedious.

## 💡 Solution

Since all Degussa transactional emails are identical, you can automatically scrape them from your inbox:

1. Connect via IMAP.
2. Filter emails from Degussa.
3. Filter out non-transactional or dca-unrelated emails
5. Extract values
- amount
- gold price
- gold quantity bought this time
- totals
from the email body.

6. Export the data as a CoinTracking-compatible CSV.
7. (not implented: write into cointracking API)

This creates a repeatable, automated ETL process for monitoring your DCA investments.

# ⚙️ Features / How it Works

1. IMAP connection to your email inbox
2. Email filtering by Degussa transactional emails
3. Parsing of transaction details
4. Output as CSV (German format currently) compatible with CoinTracking

# Optional future enhancements (TODO):

- refactor for modular configurable
- Direct integration with CoinTracking API (documentation TBD)
- Multi-language support (currently only German)
- Deployment using environment variables
- Choice between German (;=delimiter ,=decimal) or international (,=delimiter .=decimal) CSV formats

# ⚠️ Disclaimer

This script is for personal tracking and BI purposes only.
No tax advice is provided. Consult a qualified professional for tax-related questions.
Use at your own risk; Degussa may change their email format at any time.

This script is for demonstration only - not for productiv use - no warranty!

# 🛠️ Requirements

- Python 3.8+
- IMAP-accessible email account (NOT working for many freemailers)
- Libraries: imaplib, email, csv, etc.

# 📝 Usage
python imap2cointracking.py --email your@email.com --password yourpassword

CSV will be generated in the current directory.

Filter options, output format, and other parameters are configurable in the script.

# 📅 timestamps 
This script was written 2025-07-23 09:42:23 and temporarily finalized 2025-08-27 21:10:04.
Ai was used for some parts #vibecoding.
It was published and/or refactored late-2025
Github link for internal reference: https://github.com/yasuoiwakura/pyetl-imap2cointracking