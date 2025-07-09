
import streamlit as st
import pandas as pd
import altair as alt
import matplotlib.pyplot as plt
import seaborn as sns
import io
from matplotlib.backends.backend_pdf import PdfPages

# 🚚 Load merged dataset (risk + cleaned gambling data)
df = pd.read_csv("merged_gambling_data.csv")

# 🧹 Clean up
df['risk_score'] = df['risk_score'].astype(int)
df['risk_bucket'] = df['risk_bucket'].astype(str)
df.rename(columns={'gambling_days': 'deposit_days'}, inplace=True)

# ➕ Derive gambling_txn_count if missing
if 'gambling_txn_count' not in df.columns:
    df['gambling_txn_count'] = (df['gambling_txn_pct'] * df['total_txn_count']).round().astype(int)

# 🎛️ Sidebar filters
st.sidebar.header("Filters")
selected_risk = st.sidebar.selectbox("Select Risk Level", sorted(df['risk_bucket'].unique()))
min_gambling_spend = st.sidebar.checkbox("Only show users with > £100 gambling spend")

# 🧠 Filter data
filtered_df = df[df['risk_bucket'] == selected_risk]
if min_gambling_spend:
    filtered_df = filtered_df[filtered_df['gambling_spend'] > 100]

# 🧠 Header
st.title("🧠 Open Banking Risk Scoring Dashboard")
st.markdown(f"Displaying **{len(filtered_df)}** users in **{selected_risk}** category.")
st.markdown("---")

# 🧮 Risk bucket summary table
st.subheader("🧮 Overall Risk Bucket Distribution")
bucket_counts = df['risk_bucket'].value_counts().reset_index()
bucket_counts.columns = ['Risk Bucket', 'Count']
st.dataframe(bucket_counts)

# 📊 Bar chart
st.subheader("📊 Risk Bucket Bar Chart")
bar = alt.Chart(bucket_counts).mark_bar().encode(
    x=alt.X('Risk Bucket', sort=None),
    y='Count',
    tooltip=['Risk Bucket', 'Count']
).properties(width=600)
st.altair_chart(bar, use_container_width=True)

# 📋 Summary stats
st.subheader("📊 Summary Stats")
col1, col2, col3 = st.columns(3)
col1.metric("Avg Gambling Spend", f"£{filtered_df['gambling_spend'].mean():,.2f}")
col2.metric("Avg Gambling Txns", f"{filtered_df['gambling_txn_count'].mean():.1f}")
col3.metric("Avg Risk Score", f"{filtered_df['risk_score'].mean():.2f}")

# 🔍 Expandable user detail rows
st.subheader("🔍 User Risk Details")
for idx, row in filtered_df.iterrows():
    with st.expander(f"User {idx} — Score: {row['risk_score']} | Spend: £{row['gambling_spend']:.2f}"):
        st.write({
            "Risk Bucket": row['risk_bucket'],
            "Explanation": row['risk_reason'],
            "Total Txns": row['total_txn_count'],
            "Total Spend": row['total_spend'],
            "Gambling Spend": row['gambling_spend'],
            "Gambling Txns": row['gambling_txn_count'],
            "Gambling % of Txns": f"{row['gambling_txn_pct']:.2%}",
            "Gambling % of Spend": f"{row['gambling_pct_of_spend']:.2%}",
            "Deposit Days": row['deposit_days']
        })

# 📉 Correlation scatterplot with regression line
st.subheader("📉 Correlation Between Gambling Transaction % and Spend %")
fig, ax = plt.subplots(figsize=(10, 6))
sns.regplot(
    data=df,
    x='gambling_txn_pct',
    y='gambling_pct_of_spend',
    scatter_kws={'alpha': 0.5, 'color': 'royalblue'},
    line_kws={'color': 'red'},
    ax=ax
)
ax.set_title('Correlation Between Gambling Transaction % and Spend %')
ax.set_xlabel('Gambling Transactions (% of Total Transactions)')
ax.set_ylabel('Gambling Spend (% of Total Spend)')
ax.grid(True)
st.pyplot(fig)

# 📝 PDF download of the chart
pdf_bytes = io.BytesIO()
with PdfPages(pdf_bytes) as pdf:
    pdf.savefig(fig, bbox_inches='tight')
pdf_bytes.seek(0)

st.download_button(
    label="📥 Download Chart as PDF",
    data=pdf_bytes,
    file_name="gambling_txn_vs_spend_correlation.pdf",
    mime="application/pdf"
)
