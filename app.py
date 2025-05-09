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
    df = pd.read_csv(uploaded_file)
    st.success("CSV uploaded successfully!")
    st.subheader("📋 Uploaded Data Preview")
    st.dataframe(df)

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

        html_content = template.render(
            client_name=client_name,
            contact_name=dataframe['Contact Name'].iloc[0],
            contact_email=dataframe['Email'].iloc[0],
            delivery_volume=dataframe['Delivery Volume'].iloc[0],
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
