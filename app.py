import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from supabase import create_client
from datetime import date
from io import BytesIO


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Personal Expense Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ==================================================
# CUSTOM DASHBOARD DESIGN
# ==================================================

st.markdown("""
<style>
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2rem;
    }

    [data-testid="stMetric"] {
        background-color: rgba(128, 128, 128, 0.08);
        border: 1px solid rgba(128, 128, 128, 0.18);
        padding: 18px;
        border-radius: 12px;
    }

    [data-testid="stMetricLabel"] {
        font-size: 0.95rem;
    }

    [data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 700;
    }

    div[data-testid="stForm"] {
        border-radius: 12px;
    }

    .dashboard-subtitle {
        color: #808080;
        font-size: 0.95rem;
    }
</style>
""", unsafe_allow_html=True)


# ==================================================
# SESSION STATE
# ==================================================

if "access_token" not in st.session_state:
    st.session_state.access_token = None

if "refresh_token" not in st.session_state:
    st.session_state.refresh_token = None

if "user_email" not in st.session_state:
    st.session_state.user_email = None


# ==================================================
# SUPABASE CONNECTION
# ==================================================

def create_supabase_client():

    supabase_url = st.secrets["SUPABASE_URL"]
    supabase_key = st.secrets["SUPABASE_KEY"]

    return create_client(supabase_url, supabase_key)


def get_authenticated_client():

    client = create_supabase_client()

    if (
        st.session_state.get("access_token")
        and st.session_state.get("refresh_token")
    ):

        client.auth.set_session(
            st.session_state.access_token,
            st.session_state.refresh_token
        )

    return client


def get_current_user():

    client = get_authenticated_client()
    response = client.auth.get_user()

    return client, response.user.id


# ==================================================
# AUTHENTICATION FUNCTIONS
# ==================================================

def sign_up(email, password):

    client = create_supabase_client()

    return client.auth.sign_up({
        "email": email,
        "password": password
    })


def sign_in(email, password):

    client = create_supabase_client()

    return client.auth.sign_in_with_password({
        "email": email,
        "password": password
    })


def save_login_session(response):

    st.session_state.access_token = (
        response.session.access_token
    )

    st.session_state.refresh_token = (
        response.session.refresh_token
    )

    st.session_state.user_email = response.user.email


def sign_out():

    st.session_state.access_token = None
    st.session_state.refresh_token = None
    st.session_state.user_email = None

    st.rerun()


# ==================================================
# AUTHENTICATION PAGE
# ==================================================

def authentication_page():

    st.title("💰 Personal Expense Tracker")

    st.markdown(
        '<p class="dashboard-subtitle">'
        'Manage your expenses, budgets, and financial reports '
        'in one place.'
        '</p>',
        unsafe_allow_html=True
    )

    signup_tab, login_tab = st.tabs([
        "Create Account",
        "Login"
    ])

    with signup_tab:

        st.subheader("Create your account")

        with st.form("signup_form"):

            signup_email = st.text_input("Email address")

            signup_password = st.text_input(
                "Password",
                type="password"
            )

            confirm_password = st.text_input(
                "Confirm password",
                type="password"
            )

            signup_button = st.form_submit_button(
                "Create Account",
                use_container_width=True
            )

        if signup_button:

            if not signup_email or not signup_password:

                st.error(
                    "Please enter your email and password."
                )

            elif signup_password != confirm_password:

                st.error("The passwords do not match.")

            elif len(signup_password) < 8:

                st.error(
                    "Password must contain at least 8 characters."
                )

            else:

                try:

                    response = sign_up(
                        signup_email.strip(),
                        signup_password
                    )

                    if response.session:

                        save_login_session(response)

                        st.success(
                            "Account created successfully!"
                        )

                        st.rerun()

                    else:

                        st.success(
                            "Account created! Check your email "
                            "to confirm your account, then log in."
                        )

                except Exception as error:

                    st.error(f"Registration failed: {error}")

    with login_tab:

        st.subheader("Welcome back")

        with st.form("login_form"):

            login_email = st.text_input("Email address")

            login_password = st.text_input(
                "Password",
                type="password"
            )

            login_button = st.form_submit_button(
                "Login",
                use_container_width=True
            )

        if login_button:

            if not login_email or not login_password:

                st.error(
                    "Please enter your email and password."
                )

            else:

                try:

                    response = sign_in(
                        login_email.strip(),
                        login_password
                    )

                    save_login_session(response)

                    st.success("Login successful!")

                    st.rerun()

                except Exception:

                    st.error(
                        "Login failed. Check your email and password. "
                        "Confirm your email if required."
                    )


# ==================================================
# EXPENSE FUNCTIONS
# ==================================================

def load_expenses(client, user_id):

    response = (
        client.table("expenses")
        .select("*")
        .eq("user_id", user_id)
        .order("expense_date", desc=True)
        .execute()
    )

    return response.data


def add_expense(
    client,
    user_id,
    expense_date,
    category,
    description,
    amount
):

    expense_data = {
        "user_id": user_id,
        "expense_date": expense_date.isoformat(),
        "category": category,
        "description": description.strip(),
        "amount": float(amount)
    }

    client.table("expenses").insert(
        expense_data
    ).execute()


def delete_expense(client, expense_id, user_id):

    (
        client.table("expenses")
        .delete()
        .eq("id", expense_id)
        .eq("user_id", user_id)
        .execute()
    )


# ==================================================
# EDIT EXPENSE FUNCTION
# ==================================================

def update_expense(
    client,
    expense_id,
    user_id,
    expense_date,
    category,
    description,
    amount
):

    expense_data = {
        "expense_date": expense_date.isoformat(),
        "category": category,
        "description": description.strip(),
        "amount": float(amount)
    }

    (
        client.table("expenses")
        .update(expense_data)
        .eq("id", expense_id)
        .eq("user_id", user_id)
        .execute()
    )


# ==================================================
# BUDGET FUNCTIONS
# ==================================================

def load_budgets(client, user_id):

    response = (
        client.table("budgets")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )

    return response.data


def save_budget(client, user_id, budget_month, amount):

    budget_data = {
        "user_id": user_id,
        "month": budget_month,
        "amount": float(amount)
    }

    existing = (
        client.table("budgets")
        .select("id")
        .eq("user_id", user_id)
        .eq("month", budget_month)
        .execute()
    )

    if existing.data:

        (
            client.table("budgets")
            .update({"amount": float(amount)})
            .eq("id", existing.data[0]["id"])
            .eq("user_id", user_id)
            .execute()
        )

    else:

        client.table("budgets").insert(
            budget_data
        ).execute()


# ==================================================
# DATA PREPARATION
# ==================================================

def prepare_expenses_dataframe(expenses):

    columns = [
        "id",
        "user_id",
        "expense_date",
        "category",
        "description",
        "amount"
    ]

    if not expenses:

        return pd.DataFrame(columns=columns)

    df = pd.DataFrame(expenses)

    df["expense_date"] = pd.to_datetime(
        df["expense_date"]
    )

    df["amount"] = pd.to_numeric(
        df["amount"]
    )

    return df


# ==================================================
# EXPENSE SEARCH AND FILTERING
# ==================================================

def filter_expenses_dataframe(df):

    if df.empty:

        return df.copy()

    filtered_df = df.copy()

    st.subheader("🔎 Search and Filter")

    with st.expander(
        "Open search and filter options",
        expanded=True
    ):

        search_text = st.text_input(
            "Search description",
            placeholder="e.g. groceries, fuel, rent..."
        )

        categories = sorted(
            filtered_df["category"]
            .dropna()
            .unique()
            .tolist()
        )

        selected_categories = st.multiselect(
            "Filter by category",
            options=categories,
            default=categories
        )

        min_date = filtered_df["expense_date"].min().date()
        max_date = filtered_df["expense_date"].max().date()

        date_col1, date_col2 = st.columns(2)

        with date_col1:

            start_date = st.date_input(
                "Start date",
                value=min_date,
                min_value=min_date,
                max_value=max_date
            )

        with date_col2:

            end_date = st.date_input(
                "End date",
                value=max_date,
                min_value=min_date,
                max_value=max_date
            )

        minimum_amount = float(
            filtered_df["amount"].min()
        )

        maximum_amount = float(
            filtered_df["amount"].max()
        )

        amount_col1, amount_col2 = st.columns(2)

        with amount_col1:

            amount_min = st.number_input(
                "Minimum amount (₦)",
                min_value=0.0,
                max_value=max(0.0, maximum_amount),
                value=max(0.0, minimum_amount),
                step=100.0
            )

        with amount_col2:

            amount_max = st.number_input(
                "Maximum amount (₦)",
                min_value=0.0,
                max_value=max(0.0, maximum_amount),
                value=max(0.0, maximum_amount),
                step=100.0
            )

    # Search by description or category.
    if search_text.strip():

        search_value = search_text.strip().lower()

        description_match = (
            filtered_df["description"]
            .fillna("")
            .astype(str)
            .str.lower()
            .str.contains(search_value, na=False)
        )

        category_match = (
            filtered_df["category"]
            .fillna("")
            .astype(str)
            .str.lower()
            .str.contains(search_value, na=False)
        )

        filtered_df = filtered_df[
            description_match | category_match
        ]

    # Category filter.
    filtered_df = filtered_df[
        filtered_df["category"].isin(selected_categories)
    ]

    # Date filter.
    if start_date > end_date:

        st.warning(
            "The start date cannot be after the end date."
        )

        return filtered_df.iloc[0:0]

    filtered_df = filtered_df[
        (filtered_df["expense_date"].dt.date >= start_date)
        & (filtered_df["expense_date"].dt.date <= end_date)
    ]

    # Amount filter.
    if amount_min > amount_max:

        st.warning(
            "The minimum amount cannot exceed the maximum amount."
        )

        return filtered_df.iloc[0:0]

    filtered_df = filtered_df[
        (filtered_df["amount"] >= amount_min)
        & (filtered_df["amount"] <= amount_max)
    ]

    return filtered_df


# ==================================================
# EXPORT FUNCTIONS
# ==================================================

def create_csv_file(df):

    export_df = df[
        ["expense_date", "category", "description", "amount"]
    ].copy()

    export_df["expense_date"] = (
        export_df["expense_date"].dt.strftime("%Y-%m-%d")
    )

    export_df = export_df.rename(columns={
        "expense_date": "Expense Date",
        "category": "Category",
        "description": "Description",
        "amount": "Amount (NGN)"
    })

    return export_df.to_csv(index=False).encode("utf-8-sig")


def create_excel_file(df):

    export_df = df[
        ["expense_date", "category", "description", "amount"]
    ].copy()

    export_df["expense_date"] = (
        export_df["expense_date"].dt.strftime("%Y-%m-%d")
    )

    export_df = export_df.rename(columns={
        "expense_date": "Expense Date",
        "category": "Category",
        "description": "Description",
        "amount": "Amount (NGN)"
    })

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        export_df.to_excel(
            writer,
            index=False,
            sheet_name="Expense Records"
        )

        worksheet = writer.sheets["Expense Records"]

        worksheet.freeze_panes = "A2"
        worksheet.auto_filter.ref = worksheet.dimensions

        for column_cells in worksheet.columns:

            max_length = max(
                len(str(cell.value or ""))
                for cell in column_cells
            )

            worksheet.column_dimensions[
                column_cells[0].column_letter
            ].width = min(max_length + 3, 40)

    return output.getvalue()


# ==================================================
# DASHBOARD OVERVIEW
# ==================================================

def dashboard_overview(df, selected_month):

    st.header("📊 Dashboard Overview")

    st.markdown(
        '<p class="dashboard-subtitle">'
        'A clear overview of your spending activity.'
        '</p>',
        unsafe_allow_html=True
    )

    if df.empty:

        col1, col2, col3 = st.columns(3)

        col1.metric("All-Time Spending", "₦0.00")
        col2.metric("This Month's Spending", "₦0.00")
        col3.metric("Total Expenses", 0)

        st.info(
            "You have not recorded any expenses yet."
        )

        return

    month_data = df[
        df["expense_date"].dt.strftime("%Y-%m")
        == selected_month
    ]

    total_spending = float(df["amount"].sum())
    monthly_spending = float(month_data["amount"].sum())
    expense_count = len(df)

    average_expense = (
        total_spending / expense_count
        if expense_count > 0
        else 0
    )

    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "All-Time Spending",
        f"₦{total_spending:,.2f}"
    )

    col2.metric(
        "This Month's Spending",
        f"₦{monthly_spending:,.2f}"
    )

    col3.metric(
        "Total Expenses",
        f"{expense_count:,}"
    )

    col4.metric(
        "Average Expense",
        f"₦{average_expense:,.2f}"
    )

    st.divider()

    # Monthly category chart.
    if not month_data.empty:

        category_totals = (
            month_data.groupby("category")["amount"]
            .sum()
            .sort_values(ascending=False)
        )

        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:

            st.subheader("Spending by Category")

            fig, ax = plt.subplots(figsize=(8, 4))

            category_totals.plot(
                kind="bar",
                ax=ax
            )

            ax.set_xlabel("Category")
            ax.set_ylabel("Amount (₦)")
            ax.set_title("Monthly Category Spending")

            plt.xticks(rotation=35, ha="right")
            plt.tight_layout()

            st.pyplot(fig)

            plt.close(fig)

        with chart_col2:

            st.subheader("Category Breakdown")

            fig, ax = plt.subplots(figsize=(7, 4))

            category_totals.plot(
                kind="pie",
                autopct="%1.1f%%",
                ax=ax,
                ylabel=""
            )

            ax.set_title("Share of Monthly Spending")

            plt.tight_layout()

            st.pyplot(fig)

            plt.close(fig)

    else:

        st.info(
            "No category data is available for the selected month."
        )


# ==================================================
# CATEGORY SUMMARY
# ==================================================

def category_summary(df, selected_month):

    st.header("📂 Spending by Category")

    if df.empty:

        st.info(
            "Record expenses to see your category summaries."
        )

        return

    month_data = df[
        df["expense_date"].dt.strftime("%Y-%m")
        == selected_month
    ]

    if month_data.empty:

        st.info("There are no expenses for this month.")

        return

    category_totals = (
        month_data.groupby("category")["amount"]
        .sum()
        .sort_values(ascending=False)
    )

    st.dataframe(
        category_totals.rename("Total Spending (₦)"),
        use_container_width=True
    )

    fig, ax = plt.subplots(figsize=(9, 4))

    category_totals.plot(kind="bar", ax=ax)

    ax.set_title("Monthly Spending by Category")
    ax.set_xlabel("Category")
    ax.set_ylabel("Amount (₦)")

    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()

    st.pyplot(fig)

    plt.close(fig)


# ==================================================
# MONTHLY REPORT
# ==================================================

def monthly_report(df, budgets, selected_month):

    st.header("📅 Monthly Report")

    if not df.empty:

        month_data = df[
            df["expense_date"].dt.strftime("%Y-%m")
            == selected_month
        ]

        monthly_total = float(
            month_data["amount"].sum()
        )

    else:

        monthly_total = 0.0

    budget_amount = 0.0

    for budget in budgets:

        if budget["month"] == selected_month:

            budget_amount = float(budget["amount"])
            break

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Monthly Spending",
        f"₦{monthly_total:,.2f}"
    )

    col2.metric(
        "Monthly Budget",
        f"₦{budget_amount:,.2f}"
    )

    remaining = budget_amount - monthly_total

    col3.metric(
        "Remaining Budget",
        f"₦{remaining:,.2f}"
    )

    if budget_amount > 0:

        percentage = (
            monthly_total / budget_amount
        ) * 100

        st.progress(min(percentage / 100, 1.0))

        st.write(
            f"You have used {percentage:.1f}% "
            "of your monthly budget."
        )

        if monthly_total > budget_amount:

            st.warning(
                "You have exceeded your monthly budget."
            )

        else:

            st.success(
                "You are within your monthly budget."
            )

    else:

        st.info(
            "Set a monthly budget to monitor your spending."
        )


# ==================================================
# BUDGET MANAGEMENT
# ==================================================

def budget_management(
    client,
    user_id,
    budgets,
    selected_month
):

    st.header("💵 Monthly Budget")

    current_budget = 0.0

    for budget in budgets:

        if budget["month"] == selected_month:

            current_budget = float(budget["amount"])
            break

    with st.form("budget_form"):

        budget_amount = st.number_input(
            "Set your monthly budget (₦)",
            min_value=0.0,
            value=current_budget,
            step=1000.0
        )

        save_budget_button = st.form_submit_button(
            "Save Monthly Budget",
            use_container_width=True
        )

    if save_budget_button:

        if budget_amount <= 0:

            st.error(
                "Please enter a budget greater than zero."
            )

        else:

            try:

                save_budget(
                    client,
                    user_id,
                    selected_month,
                    budget_amount
                )

                st.success(
                    "Monthly budget saved successfully!"
                )

                st.rerun()

            except Exception as error:

                st.error(
                    f"Could not save budget: {error}"
                )


# ==================================================
# EXPENSE RECORDING
# ==================================================

def expense_form(client, user_id):

    st.header("➕ Record a New Expense")

    categories = [
        "Food",
        "Transport",
        "Housing",
        "Bills",
        "Shopping",
        "Health",
        "Education",
        "Entertainment",
        "Other"
    ]

    with st.form("expense_form"):

        expense_date = st.date_input(
            "Expense date",
            value=date.today()
        )

        category = st.selectbox("Category", categories)

        description = st.text_input("Description")

        amount = st.number_input(
            "Amount (₦)",
            min_value=0.01,
            value=100.00,
            step=10.00
        )

        submit_expense = st.form_submit_button(
            "Save Expense",
            use_container_width=True
        )

    if submit_expense:

        if not description.strip():

            st.error("Please enter a description.")

        else:

            try:

                add_expense(
                    client,
                    user_id,
                    expense_date,
                    category,
                    description,
                    amount
                )

                st.success(
                    "Expense recorded successfully!"
                )

                st.rerun()

            except Exception as error:

                st.error(
                    f"Could not save expense: {error}"
                )


# ==================================================
# EXPENSE RECORDS, SEARCH, FILTER, AND EXPORT
# ==================================================

def expense_records(client, expenses, user_id):

    st.header("🧾 Your Expense Records")

    if not expenses:

        st.info(
            "You haven't recorded any expenses yet."
        )

        return

    df = prepare_expenses_dataframe(expenses)

    # Apply search and filters.
    filtered_df = filter_expenses_dataframe(df)

    st.divider()

    # Summary of current filtered results.
    filtered_total = float(
        filtered_df["amount"].sum()
    )

    summary_col1, summary_col2 = st.columns(2)

    summary_col1.metric(
        "Matching Expenses",
        len(filtered_df)
    )

    summary_col2.metric(
        "Matching Total",
        f"₦{filtered_total:,.2f}"
    )

    st.subheader("Download Filtered Records")

    st.write(
        "Your downloads will contain only the expenses "
        "that match your current filters."
    )

    col1, col2 = st.columns(2)

    try:

        csv_data = create_csv_file(filtered_df)

        col1.download_button(
            label="📄 Download CSV",
            data=csv_data,
            file_name="my_filtered_expense_records.csv",
            mime="text/csv",
            use_container_width=True
        )

    except Exception as error:

        col1.error(f"CSV export failed: {error}")

    try:

        excel_data = create_excel_file(filtered_df)

        col2.download_button(
            label="📊 Download Excel",
            data=excel_data,
            file_name="my_filtered_expense_records.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            use_container_width=True
        )

    except Exception as error:

        col2.error(
            f"Excel export failed: {error}. "
            "Check that openpyxl is installed."
        )

    st.divider()

    st.subheader("Matching Expense Records")

    if filtered_df.empty:

        st.warning(
            "No expenses match your current search and filters."
        )

        return

    # Display matching expenses.
    for _, row in filtered_df.iterrows():

        expense_id = row["id"]

        with st.container(border=True):

            col1, col2 = st.columns([4, 1])

            with col1:

                st.write(f"**{row['description']}**")

                st.write(
                    f"Category: {row['category']}"
                )

                st.write(
                    f"Date: {row['expense_date'].strftime('%Y-%m-%d')}"
                )

                st.write(
                    f"Amount: ₦{float(row['amount']):,.2f}"
                )

            with col2:

                if st.button(
                    "Delete",
                    key=f"delete_{expense_id}"
                ):

                    try:

                        delete_expense(
                            client,
                            expense_id,
                            user_id
                        )

                        st.success(
                            "Expense deleted successfully."
                        )

                        st.rerun()

                    except Exception as error:

                        st.error(
                            f"Could not delete expense: {error}"
                        )


# ==================================================
# EDIT EXPENSE PAGE
# ==================================================

def edit_expense(client, expenses, user_id):

    st.header("✏️ Edit Expense")

    if not expenses:

        st.info("You have no expenses to edit yet.")
        return

    expense_options = {}

    for expense in expenses:

        label = (
            f"{expense['expense_date']} | "
            f"{expense['description']} | "
            f"₦{float(expense['amount']):,.2f} "
            f"(ID: {expense['id']})"
        )

        expense_options[label] = expense

    selected_label = st.selectbox(
        "Select the expense you want to edit",
        list(expense_options.keys())
    )

    selected_expense = expense_options[selected_label]

    expense_id = selected_expense["id"]

    current_date = date.fromisoformat(
        str(selected_expense["expense_date"])[:10]
    )

    current_category = selected_expense["category"]
    current_description = selected_expense["description"]
    current_amount = float(selected_expense["amount"])

    categories = [
        "Food",
        "Transport",
        "Housing",
        "Bills",
        "Shopping",
        "Health",
        "Education",
        "Entertainment",
        "Other"
    ]

    if current_category not in categories:
        categories.append(current_category)

    st.divider()

    with st.form("edit_expense_form"):

        new_date = st.date_input(
            "Expense Date",
            value=current_date
        )

        new_category = st.selectbox(
            "Category",
            categories,
            index=categories.index(current_category)
        )

        new_description = st.text_input(
            "Description",
            value=current_description
        )

        new_amount = st.number_input(
            "Amount (₦)",
            min_value=0.01,
            value=max(0.01, current_amount),
            step=100.0
        )

        submitted = st.form_submit_button(
            "Save Changes",
            use_container_width=True
        )

    if submitted:

        if not new_description.strip():

            st.error("Please enter a description.")

        else:

            try:

                update_expense(
                    client,
                    expense_id,
                    user_id,
                    new_date,
                    new_category,
                    new_description,
                    new_amount
                )

                st.success(
                    "Expense updated successfully!"
                )

                st.rerun()

            except Exception as error:

                st.error(
                    f"Unable to update expense: {error}"
                )


# ==================================================
# SPENDING TREND
# ==================================================

def spending_trend(df):

    st.header("📈 Spending Trend")

    if df.empty:

        st.info(
            "Record expenses to view your spending trend."
        )

        return

    monthly_totals = (
        df.groupby(
            df["expense_date"].dt.to_period("M")
        )["amount"]
        .sum()
    )

    monthly_totals.index = (
        monthly_totals.index.astype(str)
    )

    st.line_chart(monthly_totals)


# ==================================================
# MAIN DASHBOARD
# ==================================================

def expense_dashboard():

    client, user_id = get_current_user()

    st.sidebar.title("💰 Expense Tracker")

    st.sidebar.write(
        f"Logged in as: {st.session_state.user_email}"
    )

    st.sidebar.button(
        "Logout",
        on_click=sign_out
    )

    today = date.today()

    current_month = today.strftime("%Y-%m")

    month_options = sorted(
        {
            f"{year}-{month:02d}"
            for year in range(
                today.year - 2,
                today.year + 1
            )
            for month in range(1, 13)
        },
        reverse=True
    )

    st.sidebar.selectbox(
        "Select Month",
        options=month_options,
        index=month_options.index(current_month),
        key="selected_month"
    )

    selected_month = st.session_state.selected_month

    try:

        expenses = load_expenses(client, user_id)

        budgets = load_budgets(client, user_id)

    except Exception as error:

        st.error(f"Could not load your data: {error}")
        return

    df = prepare_expenses_dataframe(expenses)

    st.title("💰 Personal Expense Tracker")

    st.markdown(
        f'<p class="dashboard-subtitle">'
        f'Welcome, {st.session_state.user_email}! '
        f'Track expenses, manage budgets, and understand your spending.'
        f'</p>',
        unsafe_allow_html=True
    )

    st.divider()

    page = st.sidebar.radio(
        "Navigation",
        [
            "Dashboard",
            "Record Expense",
            "Expense Records",
            "Edit Expense",
            "Category Summary",
            "Monthly Report",
            "Budget Management",
            "Spending Trend"
        ]
    )

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

        budget_management(
            client,
            user_id,
            budgets,
            selected_month
        )

    elif page == "Spending Trend":

        spending_trend(df)


# ==================================================
# MAIN APPLICATION
# ==================================================

def main():

    if st.session_state.access_token:

        try:

            expense_dashboard()

        except Exception as error:

            st.error(f"An error occurred: {error}")

            st.button(
                "Log out",
                on_click=sign_out
            )

    else:

        authentication_page()


# ==================================================
# RUN APPLICATION
# ==================================================

main()