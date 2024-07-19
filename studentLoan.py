import streamlit as st
import pandas as pd
import math
import plotly.graph_objects as go
from fpdf import FPDF
import base64

# Set page configuration
st.set_page_config(page_title="Student Loan Repayment Calculator", layout="centered", initial_sidebar_state="expanded")

# Title
st.title("🎓 Student Loan Repayment Calculator")

# Sidebar for input data
st.sidebar.header("Input Data")
loan_amount = st.sidebar.number_input("Loan Amount", min_value=0.0, value=50000.0, step=1000.0, format="%.2f")
interest_rate = st.sidebar.number_input("Interest Rate (in %)", min_value=0.0, value=5.0, step=0.1, format="%.2f")
loan_term = st.sidebar.number_input("Loan Term (in years)", min_value=1, value=10, step=1)
extra_monthly_payment = st.sidebar.number_input("Extra Monthly Payment", min_value=0.0, value=0.0, step=50.0, format="%.2f")
extra_yearly_payment = st.sidebar.number_input("Extra Yearly Payment", min_value=0.0, value=0.0, step=500.0, format="%.2f")
extra_one_time_payment = st.sidebar.number_input("One-time Payment", min_value=0.0, value=0.0, step=1000.0, format="%.2f")

# Calculate the repayments
monthly_interest_rate = (interest_rate / 100) / 12
number_of_payments = loan_term * 12
monthly_payment = (
    loan_amount
    * (monthly_interest_rate * (1 + monthly_interest_rate) ** number_of_payments)
    / ((1 + monthly_interest_rate) ** number_of_payments - 1)
)

# Display the repayments
total_payments = monthly_payment * number_of_payments
total_interest = total_payments - loan_amount

st.write("### Repayments")
col1, col2, col3 = st.columns(3)
col1.metric(label="Monthly Repayment", value=f"${monthly_payment:,.2f}")
col2.metric(label="Total Repayment", value=f"${total_payments:,.0f}")
col3.metric(label="Total Interest", value=f"${total_interest:,.0f}")

# Create a data-frame with the payment schedule
schedule = []
remaining_balance = loan_amount

for i in range(1, number_of_payments + 1):
    interest_payment = remaining_balance * monthly_interest_rate
    principal_payment = monthly_payment - interest_payment
    remaining_balance -= principal_payment
    year = math.ceil(i / 12)
    
    if remaining_balance < 0:
        remaining_balance = 0

    schedule.append([i, monthly_payment, principal_payment, interest_payment, remaining_balance, year])
    if remaining_balance == 0:
        break

df = pd.DataFrame(
    schedule,
    columns=["Month", "Payment", "Principal", "Interest", "Remaining Balance", "Year"],
)

# Display the data-frame as a chart
st.write("### Payment Schedule")
payments_df = df[["Year", "Remaining Balance"]].groupby("Year").min()

fig = go.Figure()
fig.add_trace(go.Scatter(x=payments_df.index, y=payments_df['Remaining Balance'], mode='lines', name='Remaining Balance'))
fig.update_layout(title='Payment Schedule', xaxis_title='Year', yaxis_title='Remaining Balance')
st.plotly_chart(fig)

# Pie chart for Principal vs Interest
st.write("### Principal vs Interest")
principal_vs_interest = go.Figure(data=[go.Pie(labels=['Principal', 'Interest'], values=[loan_amount, total_interest], hole=.3)])
principal_vs_interest.update_layout(title_text="Principal vs Interest Breakdown")
st.plotly_chart(principal_vs_interest)

# Extra payments impact
st.write("### Impact of Extra Payments")
extra_schedule = []
remaining_balance = loan_amount
extra_total_paid = 0
extra_total_interest = 0
extra_months = 0

for i in range(1, number_of_payments + 1):
    if i % 12 == 0:
        remaining_balance -= extra_yearly_payment
    if i == 1:
        remaining_balance -= extra_one_time_payment

    interest_payment = remaining_balance * monthly_interest_rate
    principal_payment = monthly_payment - interest_payment + extra_monthly_payment
    remaining_balance -= principal_payment
    extra_total_paid += monthly_payment + extra_monthly_payment
    extra_total_interest += interest_payment
    extra_months += 1
    
    if remaining_balance < 0:
        remaining_balance = 0

    extra_schedule.append([extra_months, monthly_payment + extra_monthly_payment, principal_payment, interest_payment, remaining_balance])
    if remaining_balance == 0:
        break

df_extra = pd.DataFrame(
    extra_schedule,
    columns=["Month", "Payment", "Principal", "Interest", "Remaining Balance"],
)

extra_total_interest = df_extra["Interest"].sum()
extra_total_payments = extra_total_interest + loan_amount

# Calculate years and months saved
original_months = number_of_payments
extra_months = len(df_extra)
months_saved = original_months - extra_months
years_saved = months_saved // 12
months_saved = months_saved % 12
decimal_years_saved = years_saved + (months_saved / 12)
decimal_years_loan_term = round(extra_months // 12 + (extra_months % 12) / 12, 2)

st.write(f"By paying an extra {extra_monthly_payment:,.2f} per month, an extra {extra_yearly_payment:,.2f} per year, and a one-time payment of {extra_one_time_payment:,.2f}:")
col1, col2, col3 = st.columns(3)
col1.metric(label="New Total Interest", value=f"${extra_total_interest:,.2f}")
col2.metric(label="New Total Payments", value=f"${extra_total_payments:,.2f}")
col3.metric(label="Loan Term Reduction", value=f"{decimal_years_saved:.2f} years")

# Display new payment schedule with extra payments
st.write("### New Payment Schedule with Extra Payments")

# Add a column to convert months to years for the x-axis
df_extra['Year'] = df_extra['Month'] / 12

fig2 = go.Figure()
fig2.add_trace(go.Scatter(x=df_extra["Year"], y=df_extra["Remaining Balance"], mode='lines', name='Remaining Balance with Extra Payments'))
fig2.update_layout(title='New Payment Schedule with Extra Payments', xaxis_title='Year', yaxis_title='Remaining Balance')
st.plotly_chart(fig2)

# Summary table 
st.write("### Summary Table")
summary_data = {
    "Description": ["Original Loan", "With Extra Payments", "Difference"],
    "Monthly Payment": [monthly_payment, monthly_payment + extra_monthly_payment, None if extra_total_payments == total_payments else abs(monthly_payment + extra_monthly_payment - monthly_payment)],
    "Total Interest": [total_interest, extra_total_interest, None if extra_total_payments == total_payments else abs(extra_total_interest - total_interest)],
    "Total Payments": [total_payments, extra_total_payments, None if extra_total_payments == total_payments else abs(extra_total_payments - total_payments)],
    "Loan Term": [f"{loan_term} years", f"{decimal_years_loan_term} years", f"{None if extra_total_payments == total_payments else abs(decimal_years_loan_term - loan_term)} years"]
}
summary_df = pd.DataFrame(summary_data)
st.table(summary_df)


# Downloadable report
st.write("### Download Report")
pdf = FPDF()
pdf.add_page()

pdf.set_font("Arial", size=12)
pdf.cell(200, 10, txt="Student Loan Repayment Report", ln=True, align="C")

pdf.ln(10)
pdf.cell(200, 10, txt=f"Loan Amount: ${loan_amount:,.2f}", ln=True)
pdf.cell(200, 10, txt=f"Interest Rate: {interest_rate:.2f}%", ln=True)
pdf.cell(200, 10, txt=f"Loan Term: {loan_term} years", ln=True)
pdf.cell(200, 10, txt=f"Monthly Payment: ${monthly_payment:,.2f}", ln=True)
pdf.cell(200, 10, txt=f"Total Interest: ${total_interest:,.2f}", ln=True)
pdf.cell(200, 10, txt=f"Total Payments: ${total_payments:,.2f}", ln=True)

pdf.ln(10)
pdf.cell(200, 10, txt="With Extra Payments:", ln=True)
pdf.cell(200, 10, txt=f"Extra Monthly Payment: ${extra_monthly_payment:,.2f}", ln=True)
pdf.cell(200, 10, txt=f"Extra Yearly Payment: ${extra_yearly_payment:,.2f}", ln=True)
pdf.cell(200, 10, txt=f"One-time Payment: ${extra_one_time_payment:,.2f}", ln=True)
pdf.cell(200, 10, txt=f"New Total Interest: ${extra_total_interest:,.2f}", ln=True)
pdf.cell(200, 10, txt=f"New Total Payments: ${extra_total_payments:,.2f}", ln=True)
pdf.cell(200, 10, txt=f"Loan Term Reduction: {years_saved} years {months_saved} months", ln=True)

# Convert PDF to downloadable format
pdf_output = pdf.output(dest="S").encode("latin1")
b64_pdf = base64.b64encode(pdf_output).decode("latin1")
href = f'<a href="data:application/octet-stream;base64,{b64_pdf}" download="loan_repayment_report.pdf">Download Report</a>'
st.markdown(href, unsafe_allow_html=True)
