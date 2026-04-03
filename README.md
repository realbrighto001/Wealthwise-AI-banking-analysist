# 💰 WealthWise — Django Transaction Analyzer

A full-stack Django web app that analyzes your bank transaction CSV and gives you:
- 📊 Spending category breakdown with charts
- 👥 Top recipients (who you send money to most)  
- 📈 Monthly spending trends
- 🤖 AI-powered wealth management advice

---

## 🚀 Quick Setup (5 minutes)

### 1. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 2. Set up the Django database

```bash
cd wealthwise
python manage.py migrate
```

### 3. (Optional) Add AI-powered advice

Get a free API key from https://console.anthropic.com and set it:

```bash
# Mac/Linux
export ANTHROPIC_API_KEY="your-key-here"

# Windows
set ANTHROPIC_API_KEY=your-key-here
```

Without the key, the app still works with smart rule-based advice.

### 4. Run the server

```bash
python manage.py runserver
```

Open your browser at: **http://127.0.0.1:8000**

---

## 📂 CSV Format

Your CSV should have columns like:
| Date | Description | Amount | Balance |
|------|-------------|--------|---------|

Column names are **auto-detected** — works with most Nigerian bank exports:
- GTBank, First Bank, Access Bank, Zenith, UBA, Fidelity, etc.

**Common column name variations supported:**
- Date: `Date`, `Transaction Date`, `Value Date`, `Posting Date`
- Amount: `Amount`, `Debit`, `Debit Amount`, `Transaction Amount`
- Description: `Description`, `Narration`, `Details`, `Remarks`, `Memo`
- Balance: `Balance`, `Running Balance`, `Closing Balance`

---

## 📁 Project Structure

```
wealthwise/
├── manage.py
├── requirements.txt
├── sample_transactions.csv     ← Test with this file!
├── wealthwise/
│   ├── settings.py
│   └── urls.py
└── analyzer/
    ├── views.py                ← Upload & dashboard logic
    ├── services.py             ← Analysis engine + AI advice
    ├── urls.py
    └── templates/analyzer/
        ├── index.html          ← Upload page
        └── dashboard.html      ← Dashboard with charts
```

---

## 🔑 Features

- **Auto column detection** — no need to reformat your CSV
- **15+ spending categories** including Nigerian-specific merchants
- **Smart recipient extraction** from transaction descriptions
- **Interactive charts** (pie + bar) using Chart.js
- **AI advice** via Anthropic API (or rule-based fallback)
- **Dark, premium UI** with a gold aesthetic

---

## 🛠 Tech Stack

- **Backend:** Django 4.2
- **Analysis:** pandas
- **Charts:** Chart.js (CDN)
- **AI:** Anthropic Claude API (optional)
- **DB:** SQLite (just for sessions)
