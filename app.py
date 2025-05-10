import streamlit as st
import pandas as pd
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import os
import zipfile
import tempfile

st.set_page_config(page_title="Fenix Pricelist Generator", layout="wide")
st.title("📦 Fenix Rising: Monthly Pricelist Generator")

st.sidebar.header("Step 1: Upload CSV File")
uploaded_file = st.sidebar.file_uploader("Choose your pricelist CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file, encoding="utf-8", engine="python")
    df = df.dropna(axis=1, how='all')  # Remove entirely empty columns
    df = df.dropna(how='all')          # Remove entirely empty rows

    st.sidebar.header("Optional: Adjust Pricing")
    adjustment_value = st.sidebar.number_input("Adjust all prices by (R/kg)", value=0.00, step=0.10)", value="0.00")", value=0.00, step=0.10)

    if adjustment_value != 0.00:
        df["Price per kg"] = df["Price per kg"] + adjustment_value
        st.success(f"Adjusted all prices by {adjustment_value} R/kg")

    st.subheader("📋 Uploaded Data Preview")
    st.dataframe(df)

    st.download_button(
        label="📥 Download Adjusted CSV",
        data=df.to_csv(index=False),
        file_name="adjusted_pricelist.csv",
        mime="text/csv"
    )

    def render_html(dataframe, client_name):
        env = Environment(loader=FileSystemLoader("."))
        template = env.get_template("template_en.html")

        products = []
        for _, row in dataframe.iterrows():
            products.append({
                "name": row["Product"],
                "price": row["Price per kg"],
                "note": row["Note"] if pd.notnull(row["Note"]) else ""
            })

        logo_path = os.path.abspath("fenix_logo.png")

        delivery_volume_value = dataframe['Delivery Volume'].iloc[0]
        delivery_volume = "" if pd.isna(delivery_volume_value) or str(delivery_volume_value).lower() == "nan" else delivery_volume_value

        html_content = template.render(
            client_name=client_name,
            contact_name=dataframe['Contact Name'].iloc[0],
            contact_email=dataframe['Contact Email'].iloc[0],
            delivery_volume=delivery_volume,
            effective_date=dataframe['Effective Date'].iloc[0],
            products=products,
            date_today=datetime.today().strftime("%Y-%m-%d"),
            logo_path=logo_path
        )

        return html_content

    st.sidebar.header("Step 2: Select Client")
    client_list = df['Client Name'].unique()
    selected_client = st.sidebar.selectbox("Choose a client", client_list)

    if selected_client:
        client_df = df[df['Client Name'] == selected_client]
        st.subheader(f"🧾 Generate HTML for: {selected_client}")

        if st.button("📄 Generate HTML"):
            html_content = render_html(client_df, selected_client)
            st.download_button(
                label="📥 Download HTML",
                data=html_content,
                file_name=f"{selected_client}_pricelist_{datetime.today().date()}.html",
                mime="text/html"
            )

    st.subheader("📦 Batch Export for All Clients")
    if st.button("📄 Generate All as ZIP"):
        with tempfile.TemporaryDirectory() as temp_dir:
            zip_path = os.path.join(temp_dir, "all_pricelists.zip")
            with zipfile.ZipFile(zip_path, "w") as zipf:
                for client_name in client_list:
                    client_df = df[df['Client Name'] == client_name]
                    html_content = render_html(client_df, client_name)
                    file_name = f"{client_name}_pricelist_{datetime.today().date()}.html"
                    file_path = os.path.join(temp_dir, file_name)
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(html_content)
                    zipf.write(file_path, arcname=file_name)

            with open(zip_path, "rb") as f:
                st.download_button(
                    label="📥 Download All as ZIP",
                    data=f.read(),
                    file_name=f"all_pricelists_{datetime.today().date()}.zip",
                    mime="application/zip"
                )
else:
    st.info("Upload your CSV to get started.")
