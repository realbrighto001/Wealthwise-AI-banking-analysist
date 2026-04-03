import pandas as pd
import json
from collections import defaultdict
from datetime import datetime
import re


CATEGORY_KEYWORDS = {
    'Food & Dining': ['restaurant', 'food', 'eat', 'lunch', 'dinner', 'breakfast', 'cafe', 'coffee',
                      'pizza', 'burger', 'chicken', 'rice', 'suya', 'bukka', 'kitchen', 'eatery',
                      'dominos', 'kfc', 'coldstone', 'tastee', 'mr biggs'],
    'Transport': ['uber', 'bolt', 'taxi', 'transport', 'fuel', 'petrol', 'bus', 'keke', 'okada',
                  'ride', 'lagos', 'abuja', 'airfare', 'flight', 'airline'],
    'Utilities & Bills': ['electricity', 'nepa', 'ekedc', 'ibedc', 'water', 'waste', 'internet',
                          'mtn', 'airtel', 'glo', 'etisalat', '9mobile', 'dstv', 'gotv',
                          'startimes', 'netflix', 'airtime', 'data', 'subscription'],
    'Shopping': ['shop', 'store', 'market', 'jumia', 'konga', 'jiji', 'buy', 'purchase',
                 'fashion', 'cloth', 'shoe', 'bag', 'phone', 'electronics', 'mall'],
    'Healthcare': ['hospital', 'clinic', 'pharmacy', 'drug', 'health', 'doctor', 'medical',
                   'lab', 'test', 'chemist'],
    'Education': ['school', 'tuition', 'fee', 'uni', 'university', 'college', 'course',
                  'lesson', 'study', 'exam', 'book'],
    'Savings & Investment': ['save', 'invest', 'piggyvest', 'cowrywise', 'stash', 'wallet',
                              'fixed', 'stock', 'crypto', 'bitcoin', 'mutual fund'],
    'Entertainment': ['cinema', 'movie', 'concert', 'show', 'event', 'ticket', 'game',
                      'sport', 'gym', 'fitness', 'bar', 'lounge', 'club'],
    'Transfers': ['transfer', 'send', 'pay', 'payment', 'remit'],
    'Business': ['vendor', 'supplier', 'wholesale', 'invoice', 'business', 'company', 'ltd'],
}


def detect_columns(df):
    """Auto-detect column names from common bank CSV formats."""
    col_map = {}
    cols_lower = {c.lower().strip(): c for c in df.columns}

    # Date column
    for key in ['date', 'transaction date', 'trans date', 'value date', 'posting date']:
        if key in cols_lower:
            col_map['date'] = cols_lower[key]
            break

    # Amount column
    for key in ['amount', 'debit', 'debit amount', 'transaction amount', 'trans amount', 'credit']:
        if key in cols_lower:
            col_map['amount'] = cols_lower[key]
            break

    # Description column
    for key in ['description', 'narration', 'details', 'remarks', 'memo', 'transaction details', 'beneficiary']:
        if key in cols_lower:
            col_map['description'] = cols_lower[key]
            break

    # Balance column
    for key in ['balance', 'running balance', 'available balance', 'closing balance']:
        if key in cols_lower:
            col_map['balance'] = cols_lower[key]
            break

    # Credit/Debit type column
    for key in ['type', 'dr/cr', 'transaction type', 'cr/dr']:
        if key in cols_lower:
            col_map['type'] = cols_lower[key]
            break

    return col_map


def categorize_transaction(description):
    """Categorize a transaction based on its description."""
    if not description or pd.isna(description):
        return 'Uncategorized'
    desc_lower = str(description).lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in desc_lower:
                return category
    return 'Transfers'  # default


def clean_amount(value):
    """Clean and convert amount strings to float."""
    if pd.isna(value):
        return 0.0
    val_str = str(value).replace(',', '').replace('₦', '').replace('N', '').strip()
    val_str = re.sub(r'[^\d.-]', '', val_str)
    try:
        return abs(float(val_str))
    except (ValueError, TypeError):
        return 0.0


def extract_recipient(description):
    """Extract recipient name from transaction description."""
    if not description or pd.isna(description):
        return 'Unknown'
    desc = str(description)
    # Common patterns in Nigerian bank statements
    patterns = [
        r'TO\s+([A-Z][A-Z\s]+?)(?:\s+\d|\s+[-/]|$)',
        r'TRANSFER TO\s+(.+?)(?:\s+\d|$)',
        r'Payment to\s+(.+?)(?:\s+\d|$)',
        r'(?:BENEFICIARY|BEN)[:\s]+(.+?)(?:\s+\d|$)',
    ]
    for pattern in patterns:
        match = re.search(pattern, desc, re.IGNORECASE)
        if match:
            name = match.group(1).strip()
            if len(name) > 2:
                return name[:40]
    # Fallback: use first meaningful words
    words = desc.split()
    meaningful = [w for w in words[:5] if len(w) > 2 and not w.isdigit()]
    return ' '.join(meaningful[:3]) if meaningful else desc[:30]


def analyze_transactions(filepath):
    """
    Main analysis function. Returns a dict with all dashboard data.
    """
    # Read CSV with multiple encoding fallbacks
    for enc in ['utf-8', 'latin-1', 'cp1252']:
        try:
            df = pd.read_csv(filepath, encoding=enc)
            break
        except UnicodeDecodeError:
            continue

    # Drop completely empty rows/cols
    df.dropna(how='all', inplace=True)
    df.columns = df.columns.str.strip()

    col_map = detect_columns(df)

    # If we can't find key columns, return an error
    if 'amount' not in col_map and 'description' not in col_map:
        # Try to use all numeric columns as amounts
        numeric_cols = df.select_dtypes(include='number').columns.tolist()
        if numeric_cols:
            col_map['amount'] = numeric_cols[0]
        else:
            return {'error': 'Could not detect transaction columns. Please ensure your CSV has Date, Amount, and Description columns.', 'columns': list(df.columns)}

    # Standardize columns
    if 'date' in col_map:
        df['_date'] = pd.to_datetime(df[col_map['date']], errors='coerce', dayfirst=True)
    else:
        df['_date'] = pd.NaT

    if 'amount' in col_map:
        df['_amount'] = df[col_map['amount']].apply(clean_amount)
    else:
        df['_amount'] = 0.0

    if 'description' in col_map:
        df['_description'] = df[col_map['description']].fillna('').astype(str)
    else:
        # Use first text column
        text_cols = df.select_dtypes(include='object').columns.tolist()
        df['_description'] = df[text_cols[0]].fillna('').astype(str) if text_cols else ''

    if 'balance' in col_map:
        df['_balance'] = df[col_map['balance']].apply(clean_amount)

    # Filter out zero amounts
    df = df[df['_amount'] > 0].copy()

    if df.empty:
        return {'error': 'No valid transactions found. Please check your CSV file.'}

    # Categorize
    df['_category'] = df['_description'].apply(categorize_transaction)
    df['_recipient'] = df['_description'].apply(extract_recipient)

    # ── SUMMARY STATS ──────────────────────────────────────────
    total_transactions = len(df)
    total_spent = df['_amount'].sum()
    avg_transaction = df['_amount'].mean()
    max_transaction = df['_amount'].max()
    min_transaction = df['_amount'].min()

    # ── CATEGORY BREAKDOWN ─────────────────────────────────────
    cat_group = df.groupby('_category')['_amount'].agg(['sum', 'count']).reset_index()
    cat_group.columns = ['category', 'total', 'count']
    cat_group = cat_group.sort_values('total', ascending=False)
    categories = cat_group.to_dict('records')
    for c in categories:
        c['percentage'] = round((c['total'] / total_spent) * 100, 1)
        c['total'] = round(c['total'], 2)

    # ── TOP RECIPIENTS ──────────────────────────────────────────
    recip_group = df.groupby('_recipient')['_amount'].agg(['sum', 'count']).reset_index()
    recip_group.columns = ['recipient', 'total', 'count']
    recip_group = recip_group.sort_values('total', ascending=False).head(10)
    top_recipients = recip_group.to_dict('records')
    for r in top_recipients:
        r['total'] = round(r['total'], 2)
        r['percentage'] = round((r['total'] / total_spent) * 100, 1)

    # ── MONTHLY TRENDS ──────────────────────────────────────────
    monthly = []
    if not df['_date'].isna().all():
        df['_month'] = df['_date'].dt.to_period('M')
        month_group = df.groupby('_month')['_amount'].agg(['sum', 'count']).reset_index()
        month_group.columns = ['month', 'total', 'count']
        month_group = month_group.sort_values('month')
        monthly = [
            {'month': str(r['month']), 'total': round(r['total'], 2), 'count': int(r['count'])}
            for _, r in month_group.iterrows()
        ]

    # ── RECENT TRANSACTIONS ─────────────────────────────────────
    recent = df.sort_values('_date', ascending=False).head(20) if not df['_date'].isna().all() else df.head(20)
    recent_transactions = []
    for _, row in recent.iterrows():
        recent_transactions.append({
            'date': str(row['_date'].date()) if pd.notna(row['_date']) else 'N/A',
            'description': row['_description'][:60],
            'amount': round(row['_amount'], 2),
            'category': row['_category'],
            'recipient': row['_recipient'],
        })

    # ── LARGEST TRANSACTIONS ────────────────────────────────────
    largest = df.nlargest(5, '_amount')[['_date', '_description', '_amount', '_category']].copy()
    largest_transactions = [
        {
            'date': str(r['_date'].date()) if pd.notna(r['_date']) else 'N/A',
            'description': r['_description'][:60],
            'amount': round(r['_amount'], 2),
            'category': r['_category'],
        }
        for _, r in largest.iterrows()
    ]

    return {
        'summary': {
            'total_transactions': total_transactions,
            'total_spent': round(total_spent, 2),
            'average_transaction': round(avg_transaction, 2),
            'max_transaction': round(max_transaction, 2),
            'min_transaction': round(min_transaction, 2),
        },
        'categories': categories,
        'top_recipients': top_recipients,
        'monthly_trends': monthly,
        'recent_transactions': recent_transactions,
        'largest_transactions': largest_transactions,
        'columns_detected': col_map,
        'all_columns': list(df.columns),
    }


def generate_ai_advice(analysis_data):
    """Generate AI wealth advice using Anthropic API."""
    import urllib.request
    import json
    from django.conf import settings

    api_key = settings.ANTHROPIC_API_KEY
    if not api_key:
        return generate_rule_based_advice(analysis_data)

    summary = analysis_data.get('summary', {})
    categories = analysis_data.get('categories', [])
    top_recipients = analysis_data.get('top_recipients', [])
    monthly = analysis_data.get('monthly_trends', [])

    # Build a concise prompt
    top_cats = ', '.join([f"{c['category']} ({c['percentage']}%)" for c in categories[:5]])
    top_recip = ', '.join([f"{r['recipient']} (₦{r['total']:,.0f})" for r in top_recipients[:3]])
    monthly_summary = ', '.join([f"{m['month']}: ₦{m['total']:,.0f}" for m in monthly[-4:]]) if monthly else 'N/A'

    prompt = f"""You are a personal finance advisor for a Nigerian user. Analyze their spending and give practical, actionable wealth management advice.

Transaction Summary:
- Total transactions analyzed: {summary.get('total_transactions', 0)}
- Total amount spent: ₦{summary.get('total_spent', 0):,.2f}
- Average transaction: ₦{summary.get('average_transaction', 0):,.2f}
- Largest single transaction: ₦{summary.get('max_transaction', 0):,.2f}

Top Spending Categories: {top_cats}
Top Recipients: {top_recip}
Recent Monthly Spending: {monthly_summary}

Provide:
1. 3 key observations about their spending patterns
2. 3 specific actionable tips to save more money
3. 1 investment recommendation relevant to Nigeria (PiggyVest, Cowrywise, stocks, etc.)
4. A wealth-building goal they should aim for

Keep it friendly, specific, and practical. Use ₦ for currency. Be encouraging but honest."""

    try:
        payload = json.dumps({
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": prompt}]
        }).encode('utf-8')

        req = urllib.request.Request(
            'https://api.anthropic.com/v1/messages',
            data=payload,
            headers={
                'Content-Type': 'application/json',
                'x-api-key': api_key,
                'anthropic-version': '2023-06-01'
            }
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            return result['content'][0]['text']
    except Exception as e:
        return generate_rule_based_advice(analysis_data)


def generate_rule_based_advice(analysis_data):
    """Fallback rule-based advice when no API key is set."""
    summary = analysis_data.get('summary', {})
    categories = analysis_data.get('categories', [])
    top_recipients = analysis_data.get('top_recipients', [])

    advice = []
    total_spent = summary.get('total_spent', 0)

    # Find biggest spending category
    if categories:
        top_cat = categories[0]
        advice.append(f"📊 **Your biggest spending area is {top_cat['category']}**, accounting for {top_cat['percentage']}% of your total spend (₦{top_cat['total']:,.2f}). Consider setting a monthly budget for this category.")

    # Check if transfers dominate
    transfer_cats = [c for c in categories if c['category'] == 'Transfers']
    if transfer_cats and transfer_cats[0]['percentage'] > 40:
        advice.append(f"💸 **Over 40% of your money goes to transfers.** Review who you're sending money to most — are all these payments necessary or recurring obligations you could renegotiate?")

    # Top recipient insight
    if top_recipients:
        top = top_recipients[0]
        advice.append(f"👤 **Your highest recipient is '{top['recipient']}' with ₦{top['total']:,.2f}** across {top['count']} transactions. Make sure this aligns with your financial goals.")

    # General savings advice
    savings_pct = next((c['percentage'] for c in categories if 'Savings' in c['category']), 0)
    if savings_pct < 10:
        advice.append("💰 **You're saving less than 10% of your spending.** Try the 50/30/20 rule: 50% needs, 30% wants, 20% savings & investments.")
    else:
        advice.append(f"✅ **Great job! You're allocating {savings_pct}% to savings/investments.** Keep it up and aim to increase this to 25% over the next 6 months.")

    advice.append("📈 **Investment tip:** Consider opening a PiggyVest or Cowrywise account to automate savings. Even saving ₦5,000/week adds up to ₦260,000/year in interest-earning accounts.")
    advice.append("🎯 **Goal:** Build an emergency fund of 3–6 months of expenses before making large investments. Based on your spending, aim for ₦{:,.0f} – ₦{:,.0f}.".format(total_spent * 3, total_spent * 6))

    # Set ANTHROPIC_API_KEY note
    advice.append("\n> 💡 **Tip:** Set your `ANTHROPIC_API_KEY` environment variable to get personalized AI-powered advice tailored specifically to your spending patterns!")

    return '\n\n'.join(advice)
