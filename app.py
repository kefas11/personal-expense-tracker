import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from supabase import create_client
from datetime import date
from io import BytesIO

# ==========================================================
# PAGE CONFIGURATION
# ==========================================================
st.set_page_config(
    page_title="Personal Expense Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================================
# BRAND COLOURS AND APPEARANCE
# ==========================================================
if "appearance" not in st.session_state:
    st.session_state.appearance = "Light"

appearance = st.session_state.appearance
DARK = appearance == "Dark"

BG = "#101B18" if DARK else "#F8F6F0"
SURFACE = "#1B2924" if DARK else "#FFFFFF"
TEXT = "#F4F1E8" if DARK else "#202A27"
MUTED = "#B5C0B8" if DARK else "#68736C"
BORDER = "#40534A" if DARK else "#E5E5DC"
EMERALD = "#103B35"
CHAMPAGNE = "#D6BD91"
SIDEBAR = "#17231F" if DARK else "#103B35"

st.markdown(f"""
<style>
:root {{
    --app-bg: {BG};
    --surface: {SURFACE};
    --text: {TEXT};
    --muted: {MUTED};
    --border: {BORDER};
    --emerald: {EMERALD};
    --champagne: {CHAMPAGNE};
}}
.stApp {{ background: var(--app-bg); color: var(--text); }}
.block-container {{ padding-top: 2rem; padding-bottom: 3rem; max-width: 1500px; }}
[data-testid="stHeader"] {{ background: transparent; }}
[data-testid="stSidebar"] {{
    background: {SIDEBAR};
    border-right: 1px solid {BORDER};
}}
[data-testid="stSidebar"] * {{ color: #F8F6F0 !important; }}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{ color: #D6DED8 !important; }}

/* SIDEBAR REPORT-MONTH SELECTOR ONLY: NAVY BACKGROUND, WHITE TEXT */
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] > div {{
    background-color: #172A46 !important;
    border: 1px solid #D6BD91 !important;
}}
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] * {{
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}}
[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] svg {{
    fill: #FFFFFF !important;
}}

/* MONTH OPTIONS WHEN THE SIDEBAR DROPDOWN IS OPEN */
[data-baseweb="popover"] {{
    background-color: #172A46 !important;
}}
[data-baseweb="popover"] [role="listbox"] {{
    background-color: #172A46 !important;
}}
[data-baseweb="popover"] [role="option"] {{
    background-color: #172A46 !important;
    color: #FFFFFF !important;
}}
[data-baseweb="popover"] [role="option"] * {{
    color: #FFFFFF !important;
    -webkit-text-fill-color: #FFFFFF !important;
}}
[data-baseweb="popover"] [role="option"]:hover,
[data-baseweb="popover"] [role="option"][aria-selected="true"] {{
    background-color: #294568 !important;
    color: #FFFFFF !important;
}}

/* MONTHLY REPORT PERIOD */
.report-period {{
    background: #172A46 !important;
    color: #FFFFFF !important;
    border: 1px solid #D6BD91;
    border-left: 5px solid #D6BD91;
    border-radius: 12px;
    padding: 14px 18px;
    margin: 12px 0 22px;
    font-size: 1.1rem;
    font-weight: 700;
}}

h1, h2, h3, h4 {{ color: var(--text) !important; letter-spacing: -0.025em; }}
p, label, .stMarkdown {{ color: var(--text); }}
.dashboard-subtitle {{ color: var(--muted) !important; font-size: 1rem; }}
.brand-kicker {{
    color: var(--champagne); font-size: .76rem; font-weight: 800;
    letter-spacing: .22em; text-transform: uppercase; margin-bottom: .45rem;
}}
.brand-title {{ font-size: clamp(2rem, 4vw, 3rem); font-weight: 800;
    line-height: 1.08; color: var(--text); margin: 0; }}
.brand-rule {{ width: 74px; height: 4px; background: var(--champagne);
    border-radius: 8px; margin: 1rem 0 1.1rem; }}
[data-testid="stMetric"] {{
    background: var(--surface); border: 1px solid var(--border);
    padding: 20px 22px; border-radius: 16px;
    box-shadow: 0 5px 18px rgba(0,0,0,.045);
}}
[data-testid="stMetricLabel"] {{ color: var(--muted) !important; font-weight: 600; }}
[data-testid="stMetricValue"] {{ color: var(--text) !important; font-weight: 800; }}
[data-testid="stMetricDelta"] {{ font-size: .85rem; }}
div[data-testid="stForm"], [data-testid="stExpander"] {{
    border: 1px solid var(--border); border-radius: 14px;
    background: var(--surface);
}}
.stTextInput input, .stNumberInput input, .stDateInput input,
.stSelectbox [data-baseweb="select"], .stMultiSelect [data-baseweb="select"] {{
    border-radius: 10px;
}}
.stButton > button, .stFormSubmitButton > button, .stDownloadButton > button {{
    border-radius: 10px; border: 1px solid var(--champagne);
    font-weight: 700; min-height: 2.7rem;
}}
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {{
    background: var(--emerald); color: #FFFFFF; border: 1px solid var(--champagne);
}}
hr {{ border-color: var(--border); }}
[data-testid="stDataFrame"] {{ border: 1px solid var(--border); border-radius: 12px; }}
.auth-panel {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 20px; padding: clamp(1rem, 3vw, 2rem);
}}
.small-note {{ color: var(--muted); font-size: .88rem; }}
@media (max-width: 700px) {{
    .block-container {{ padding: 1rem .8rem 2rem; }}
    [data-testid="stMetric"] {{ padding: 13px; }}
}}
</style>
""", unsafe_allow_html=True)

# ==========================================================
# SESSION STATE
# ==========================================================
for key, default in {
    "access_token": None,
    "refresh_token": None,
    "user_email": None
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ==========================================================
# SHARED UI HELPERS
# ==========================================================
def brand_header(subtitle="Manage your expenses, budgets and financial reports in one place."):
    st.markdown(
        f"""
        <div class="brand-title">Personal Expense Tracker</div>
        <div class="brand-rule"></div>
        <p class="dashboard-subtitle">{subtitle}</p>
        """,
        unsafe_allow_html=True
    )

def currency(value):
    return f"₦{float(value):,.2f}"

def appearance_control():
    st.sidebar.markdown("### Appearance")
    st.sidebar.selectbox(
        "Choose your display",
        ["Light", "Dark"],
        key="appearance",
        label_visibility="collapsed"
    )

# ==========================================================
# SUPABASE CONNECTION AND AUTHENTICATION
# ==========================================================
def create_supabase_client():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )

def get_authenticated_client():
    client = create_supabase_client()
    access = st.session_state.get("access_token")
    refresh = st.session_state.get("refresh_token")
    if access and refresh:
        client.auth.set_session(access, refresh)
    return client

def get_current_user():
    client = get_authenticated_client()
    response = client.auth.get_user()
    if not response.user:
        raise RuntimeError("Your login session has expired. Please log in again.")
    return client, response.user.id

def sign_up(email, password):
    return create_supabase_client().auth.sign_up({
        "email": email, "password": password
    })

def sign_in(email, password):
    return create_supabase_client().auth.sign_in_with_password({
        "email": email, "password": password
    })

def save_login_session(response):
    if not response.session or not response.user:
        raise RuntimeError("No active session was returned. Confirm your email if required.")
    st.session_state.access_token = response.session.access_token
    st.session_state.refresh_token = response.session.refresh_token
    st.session_state.user_email = response.user.email

def sign_out():
    for key in ("access_token", "refresh_token", "user_email"):
        st.session_state[key] = None
    st.rerun()

# ==========================================================
# AUTHENTICATION PAGE
# ==========================================================
def authentication_page():
    appearance_control()
    _, center, _ = st.columns([1, 1.5, 1])
    with center:
        st.markdown('<div class="auth-panel">', unsafe_allow_html=True)
        brand_header("A more considered way to manage your money.")
        signup_tab, login_tab = st.tabs(["Create Account", "Login"])

        with signup_tab:
            st.subheader("Create your account")
            with st.form("signup_form"):
                email = st.text_input("Email address", key="signup_email")
                password = st.text_input("Password", type="password", key="signup_password")
                confirm = st.text_input("Confirm password", type="password")
                submitted = st.form_submit_button("Create Account", use_container_width=True)
            if submitted:
                if not email.strip() or not password:
                    st.error("Please enter your email and password.")
                elif password != confirm:
                    st.error("The passwords do not match.")
                elif len(password) < 8:
                    st.error("Password must contain at least 8 characters.")
                else:
                    try:
                        response = sign_up(email.strip(), password)
                        if response.session:
                            save_login_session(response)
                            st.success("Account created successfully.")
                            st.rerun()
                        else:
                            st.success("Account created. Check your email to confirm your account, then log in.")
                    except Exception as error:
                        st.error(f"Registration failed: {error}")

        with login_tab:
            st.subheader("Welcome back")
            with st.form("login_form"):
                email = st.text_input("Email address", key="login_email")
                password = st.text_input("Password", type="password", key="login_password")
                submitted = st.form_submit_button("Login", use_container_width=True)
            if submitted:
                if not email.strip() or not password:
                    st.error("Please enter your email and password.")
                else:
                    try:
                        response = sign_in(email.strip(), password)
                        save_login_session(response)
                        st.success("Login successful.")
                        st.rerun()
                    except Exception:
                        st.error("Login failed. Check your email and password, and confirm your email if required.")
        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown('<p class="small-note" style="text-align:center">Your personal finances, organised with clarity.</p>', unsafe_allow_html=True)

# ==========================================================
# DATABASE OPERATIONS
# ==========================================================
def load_expenses(client, user_id):
    return (client.table("expenses").select("*")
            .eq("user_id", user_id)
            .order("expense_date", desc=True).execute().data)

def add_expense(client, user_id, expense_date, category, description, amount):
    data = {
        "user_id": user_id, "expense_date": expense_date.isoformat(),
        "category": category, "description": description.strip(),
        "amount": float(amount)
    }
    client.table("expenses").insert(data).execute()

def delete_expense(client, expense_id, user_id):
    (client.table("expenses").delete()
     .eq("id", expense_id).eq("user_id", user_id).execute())

def update_expense(client, expense_id, user_id, expense_date, category, description, amount):
    data = {
        "expense_date": expense_date.isoformat(), "category": category,
        "description": description.strip(), "amount": float(amount)
    }
    (client.table("expenses").update(data)
     .eq("id", expense_id).eq("user_id", user_id).execute())

def load_budgets(client, user_id):
    return client.table("budgets").select("*").eq("user_id", user_id).execute().data

def save_budget(client, user_id, budget_month, amount):
    data = {"user_id": user_id, "month": budget_month, "amount": float(amount)}
    existing = (client.table("budgets").select("id")
                .eq("user_id", user_id).eq("month", budget_month).execute())
    if existing.data:
        (client.table("budgets").update({"amount": float(amount)})
         .eq("id", existing.data[0]["id"]).eq("user_id", user_id).execute())
    else:
        client.table("budgets").insert(data).execute()

# ==========================================================
# DATA PREPARATION AND FILTERS
# ==========================================================
def prepare_expenses_dataframe(expenses):
    columns = ["id", "user_id", "expense_date", "category", "description", "amount"]
    if not expenses:
        return pd.DataFrame(columns=columns)
    df = pd.DataFrame(expenses)
    df["expense_date"] = pd.to_datetime(df["expense_date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    return df

def filter_expenses_dataframe(df):
    if df.empty:
        return df.copy()
    result = df.copy()
    st.subheader("Search and filter")
    with st.expander("Search and filter options", expanded=True):
        search = st.text_input("Search description or category", placeholder="e.g. groceries, fuel, rent")
        categories = sorted(result["category"].dropna().unique().tolist())
        selected = st.multiselect("Categories", categories, default=categories)
        min_date = result["expense_date"].min().date()
        max_date = result["expense_date"].max().date()
        c1, c2 = st.columns(2)
        with c1:
            start = st.date_input("Start date", min_date, min_value=min_date, max_value=max_date)
        with c2:
            end = st.date_input("End date", max_date, min_value=min_date, max_value=max_date)
        low = max(0.0, float(result["amount"].min()))
        high = max(low, float(result["amount"].max()))
        a1, a2 = st.columns(2)
        with a1:
            amount_min = st.number_input("Minimum amount (₦)", min_value=0.0, max_value=high, value=low, step=100.0)
        with a2:
            amount_max = st.number_input("Maximum amount (₦)", min_value=0.0, max_value=high, value=high, step=100.0)
    if search.strip():
        term = search.strip().lower()
        mask = (result["description"].fillna("").astype(str).str.lower().str.contains(term, na=False)
                | result["category"].fillna("").astype(str).str.lower().str.contains(term, na=False))
        result = result[mask]
    result = result[result["category"].isin(selected)]
    if start > end or amount_min > amount_max:
        st.warning("Check your date and amount ranges.")
        return result.iloc[0:0]
    result = result[
        result["expense_date"].dt.date.between(start, end)
        & result["amount"].between(amount_min, amount_max)
    ]
    return result

# ==========================================================
# EXPORTS
# ==========================================================
def export_ready_dataframe(df):
    out = df[["expense_date", "category", "description", "amount"]].copy()
    out["expense_date"] = out["expense_date"].dt.strftime("%Y-%m-%d")
    return out.rename(columns={
        "expense_date": "Expense Date", "category": "Category",
        "description": "Description", "amount": "Amount (NGN)"
    })

def create_csv_file(df):
    return export_ready_dataframe(df).to_csv(index=False).encode("utf-8-sig")

def create_excel_file(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        export_ready_dataframe(df).to_excel(writer, index=False, sheet_name="Expense Records")
        ws = writer.sheets["Expense Records"]
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions
        for cells in ws.columns:
            width = max(len(str(cell.value or "")) for cell in cells)
            ws.column_dimensions[cells[0].column_letter].width = min(width + 3, 40)
    return output.getvalue()

# ==========================================================
# CHART HELPER
# ==========================================================
def style_axes(ax):
    ax.set_facecolor(SURFACE)
    ax.tick_params(colors=TEXT)
    ax.xaxis.label.set_color(TEXT)
    ax.yaxis.label.set_color(TEXT)
    ax.title.set_color(TEXT)
    for spine in ax.spines.values():
        spine.set_color(BORDER)

def show_bar_chart(series, title, xlabel="Category", ylabel="Amount (₦)"):
    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor(SURFACE)
    series.plot(kind="bar", ax=ax, color=EMERALD)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.tick_params(axis="x", rotation=35)
    style_axes(ax)
    plt.tight_layout()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

# ==========================================================
# DASHBOARD AND REPORTS
# ==========================================================
def dashboard_overview(df, selected_month):
    st.subheader("Dashboard overview")
    st.markdown('<p class="dashboard-subtitle">A clear overview of your spending activity.</p>', unsafe_allow_html=True)
    month_data = df[df["expense_date"].dt.strftime("%Y-%m") == selected_month] if not df.empty else df
    total = float(df["amount"].sum()) if not df.empty else 0.0
    monthly = float(month_data["amount"].sum()) if not month_data.empty else 0.0
    count = len(df)
    average = total / count if count else 0.0
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("All-time spending", currency(total))
    c2.metric("This month's spending", currency(monthly))
    c3.metric("Total expenses", f"{count:,}")
    c4.metric("Average expense", currency(average))
    st.divider()
    if month_data.empty:
        st.info("No expenses recorded for the selected month yet.")
        return
    totals = month_data.groupby("category")["amount"].sum().sort_values(ascending=False)
    left, right = st.columns(2)
    with left:
        st.markdown("#### Spending by category")
        show_bar_chart(totals, "Monthly category spending")
    with right:
        st.markdown("#### Category breakdown")
        fig, ax = plt.subplots(figsize=(7, 4))
        fig.patch.set_facecolor(SURFACE)
        totals.plot(kind="pie", autopct="%1.1f%%", ax=ax, ylabel="")
        ax.set_title("Share of monthly spending", color=TEXT)
        ax.set_facecolor(SURFACE)
        plt.tight_layout()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

def monthly_report(df, budgets, selected_month):
    st.subheader("Monthly report")

    # Display the selected month clearly
    month_name = pd.to_datetime(
        selected_month + "-01"
    ).strftime("%B %Y")

    st.markdown(
        f'<div class="report-period">Reporting period: {month_name}</div>',
        unsafe_allow_html=True
    )

    month_data = (
        df[df["expense_date"].dt.strftime("%Y-%m") == selected_month]
        if not df.empty else df
    )

    spent = float(month_data["amount"].sum()) if not month_data.empty else 0.0

    budget = next(
        (float(b["amount"]) for b in budgets
         if b["month"] == selected_month),
        0.0
    )

    remaining = budget - spent

    c1, c2, c3 = st.columns(3)

    c1.metric("Monthly spending", currency(spent))
    c2.metric("Monthly budget", currency(budget))
    c3.metric(
        "Remaining budget",
        currency(remaining),
        delta="Over budget" if remaining < 0 else None,
        delta_color="inverse"
    )

    st.divider()

    if budget > 0:
        percentage = spent / budget * 100

        st.progress(min(percentage / 100, 1.0))

        st.caption(
            f"You have used {percentage:.1f}% of your monthly budget."
        )

        if spent > budget:
            st.warning("You have exceeded your monthly budget.")
        else:
            st.success("You are within your monthly budget.")

    else:
        st.info("Set a monthly budget to monitor your spending.")

    if month_data.empty:
        st.info(f"No expenses recorded for {month_name}.")
    else:
        st.markdown(f"#### Expense activity for {month_name}")

        report_table = month_data[
            ["expense_date", "category", "description", "amount"]
        ].copy()

        report_table["expense_date"] = (
            report_table["expense_date"].dt.strftime("%d %b %Y")
        )

        report_table["amount"] = report_table["amount"].apply(currency)

        report_table.columns = [
            "Date", "Category", "Description", "Amount"
        ]

        st.dataframe(
            report_table,
            use_container_width=True,
            hide_index=True
        )

def category_summary(df, selected_month):
    st.subheader("Spending by category")
    if df.empty:
        st.info("Record expenses to see your category summaries.")
        return
    month_data = df[df["expense_date"].dt.strftime("%Y-%m") == selected_month]
    if month_data.empty:
        st.info("There are no expenses for this month.")
        return
    totals = month_data.groupby("category")["amount"].sum().sort_values(ascending=False)
    display = totals.rename("Total Spending (₦)").reset_index()
    st.dataframe(display, use_container_width=True, hide_index=True)
    show_bar_chart(totals, "Monthly spending by category")

# ==========================================================
# BUDGET AND EXPENSE FORMS
# ==========================================================
def budget_management(client, user_id, budgets, selected_month):
    st.subheader("Monthly budget")
    current = next((float(b["amount"]) for b in budgets if b["month"] == selected_month), 0.0)
    st.caption(f"Set a spending limit for {selected_month}.")
    with st.form("budget_form"):
        amount = st.number_input("Set your monthly budget (₦)", min_value=0.0, value=current, step=1000.0)
        submitted = st.form_submit_button("Save monthly budget", use_container_width=True)
    if submitted:
        if amount <= 0:
            st.error("Please enter a budget greater than zero.")
        else:
            try:
                save_budget(client, user_id, selected_month, amount)
                st.success("Monthly budget saved successfully.")
                st.rerun()
            except Exception as error:
                st.error(f"Could not save budget: {error}")

def expense_form(client, user_id):
    st.subheader("Record a new expense")
    categories = ["Food", "Transport", "Housing", "Bills", "Shopping", "Health", "Education", "Entertainment", "Other"]
    with st.form("expense_form"):
        expense_date = st.date_input("Expense date", value=date.today())
        category = st.selectbox("Category", categories)
        description = st.text_input("Description")
        amount = st.number_input("Amount (₦)", min_value=0.01, value=100.0, step=10.0)
        submitted = st.form_submit_button("Save expense", use_container_width=True)
    if submitted:
        if not description.strip():
            st.error("Please enter a description.")
        else:
            try:
                add_expense(client, user_id, expense_date, category, description, amount)
                st.success("Expense recorded successfully.")
                st.rerun()
            except Exception as error:
                st.error(f"Could not save expense: {error}")

# ==========================================================
# EXPENSE RECORDS, EDITING AND EXPORTS
# ==========================================================
def expense_records(client, expenses, user_id):
    st.subheader("Your expense records")
    if not expenses:
        st.info("You haven't recorded any expenses yet.")
        return
    df = prepare_expenses_dataframe(expenses)
    filtered = filter_expenses_dataframe(df)
    st.divider()
    c1, c2 = st.columns(2)
    c1.metric("Matching expenses", len(filtered))
    c2.metric("Matching total", currency(filtered["amount"].sum()))
    st.markdown("#### Download filtered records")
    d1, d2 = st.columns(2)
    d1.download_button("Download CSV", create_csv_file(filtered), "my_filtered_expense_records.csv", "text/csv", use_container_width=True)
    try:
        excel = create_excel_file(filtered)
        d2.download_button("Download Excel", excel, "my_filtered_expense_records.xlsx",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           use_container_width=True)
    except Exception as error:
        d2.error(f"Excel export failed: {error}")
    st.divider()
    st.markdown("#### Matching expense records")
    if filtered.empty:
        st.warning("No expenses match your current search and filters.")
        return
    for _, row in filtered.iterrows():
        expense_id = row["id"]
        with st.container(border=True):
            left, right = st.columns([5, 1])
            with left:
                st.markdown(f"**{row['description']}**")
                st.caption(f"{row['category']}  ·  {row['expense_date'].strftime('%Y-%m-%d')}")
                st.markdown(f"**{currency(row['amount'])}**")
            with right:
                if st.button("Delete", key=f"delete_{expense_id}"):
                    try:
                        delete_expense(client, expense_id, user_id)
                        st.success("Expense deleted.")
                        st.rerun()
                    except Exception as error:
                        st.error(f"Could not delete expense: {error}")

def edit_expense(client, expenses, user_id):
    st.subheader("Edit an expense")
    if not expenses:
        st.info("You have no expenses to edit yet.")
        return
    options = {}
    for item in expenses:
        label = f"{item['expense_date']} | {item['description']} | {currency(item['amount'])} (ID: {item['id']})"
        options[label] = item
    label = st.selectbox("Select the expense you want to edit", list(options))
    item = options[label]
    categories = ["Food", "Transport", "Housing", "Bills", "Shopping", "Health", "Education", "Entertainment", "Other"]
    if item["category"] not in categories:
        categories.append(item["category"])
    with st.form("edit_expense_form"):
        new_date = st.date_input("Expense date", date.fromisoformat(str(item["expense_date"])[:10]))
        new_category = st.selectbox("Category", categories, index=categories.index(item["category"]))
        new_description = st.text_input("Description", item["description"])
        new_amount = st.number_input("Amount (₦)", min_value=0.01, value=max(0.01, float(item["amount"])), step=100.0)
        submitted = st.form_submit_button("Save changes", use_container_width=True)
    if submitted:
        if not new_description.strip():
            st.error("Please enter a description.")
        else:
            try:
                update_expense(client, item["id"], user_id, new_date, new_category, new_description, new_amount)
                st.success("Expense updated successfully.")
                st.rerun()
            except Exception as error:
                st.error(f"Unable to update expense: {error}")

def spending_trend(df):
    st.subheader("Spending trend")
    if df.empty:
        st.info("Record expenses to view your spending trend.")
        return
    totals = df.groupby(df["expense_date"].dt.to_period("M"))["amount"].sum()
    totals.index = totals.index.astype(str)
    st.line_chart(totals)

# ==========================================================
# MAIN DASHBOARD
# ==========================================================
def expense_dashboard():
    client, user_id = get_current_user()
    appearance_control()
    st.sidebar.markdown("---")
    st.sidebar.markdown("## 💰 Expense Tracker")
    st.sidebar.caption(f"Signed in as {st.session_state.user_email}")
    st.sidebar.button("Logout", on_click=sign_out, use_container_width=True)
    today = date.today()
    current_month = today.strftime("%Y-%m")
    month_options = sorted({
        f"{year}-{month:02d}"
        for year in range(today.year - 2, today.year + 1)
        for month in range(1, 13)
    }, reverse=True)
    st.sidebar.selectbox("Report month", month_options, index=month_options.index(current_month), key="selected_month")
    selected_month = st.session_state.selected_month
    try:
        expenses = load_expenses(client, user_id)
        budgets = load_budgets(client, user_id)
    except Exception as error:
        st.error(f"Could not load your data: {error}")
        return
    df = prepare_expenses_dataframe(expenses)
    brand_header(f"Welcome back, {st.session_state.user_email}. Your finances, at a glance.")
    st.divider()
    page = st.sidebar.radio("Navigation", [
        "Dashboard", "Record Expense", "Expense Records", "Edit Expense",
        "Category Summary", "Monthly Report", "Budget Management", "Spending Trend"
    ])
    if page == "Dashboard":
        dashboard_overview(df, selected_month)
        st.divider()
        monthly_report(df, budgets, selected_month)
    elif page == "Record Expense":
        expense_form(client, user_id)
    elif page == "Expense Records":
        expense_records(client, expenses, user_id)
    elif page == "Edit Expense":
        edit_expense(client, expenses, user_id)
    elif page == "Category Summary":
        category_summary(df, selected_month)
    elif page == "Monthly Report":
        monthly_report(df, budgets, selected_month)
    elif page == "Budget Management":
        budget_management(client, user_id, budgets, selected_month)
    elif page == "Spending Trend":
        spending_trend(df)

# ==========================================================
# RUN APPLICATION
# ==========================================================
def main():
    if st.session_state.access_token:
        try:
            expense_dashboard()
        except Exception as error:
            st.error(f"An error occurred: {error}")
            st.button("Log out", on_click=sign_out)
    else:
        authentication_page()

main()
