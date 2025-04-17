# -*- coding: utf-8 -*-
"""CustomerOrderDetail.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1GVaZtbV4Ld2MRESb0i4SkVCJBsyJck1n
"""

import streamlit as st
import pandas as pd
import numpy as np
import re
import io
import base64
from datetime import datetime

st.set_page_config(
    page_title="Excel Data Processor",
    page_icon="📊",
    layout="wide"
)

def clean_data(df):
    """Clean and transform the data from the uploaded Excel file."""
    cleaned_df = df.copy()

    # Forward fill the customer name and item type
    cleaned_df['Customer_Name'] = cleaned_df['Type'].where(cleaned_df['Type'] != 'Item')
    cleaned_df['Type'] = cleaned_df['Type'].where(cleaned_df['Type'] == 'Item')
    cleaned_df['Customer_Name'] = cleaned_df['Customer_Name'].ffill()

    # Regex pattern for date in 'Shipment Date' column
    date_pattern = r'\d{2}-\d{2}-\d{2}'

    # Separate Customer ID and Shipment Date
    cleaned_df['CID'] = cleaned_df['Shipment Date'].where(~cleaned_df['Shipment Date'].str.contains(date_pattern, na=False))
    cleaned_df['Shipment_Date'] = cleaned_df['Shipment Date'].where(cleaned_df['Shipment Date'].str.contains(date_pattern, na=False))

    # Forward fill CID and Shipment Date
    cleaned_df['CID'] = cleaned_df['CID'].ffill()
    cleaned_df['Shipment_Date'] = pd.to_datetime(cleaned_df['Shipment_Date'].ffill(), errors='coerce')

    # Extract Order_No and Order_Date from Description
    order_pattern = r"(\d{5,})\s+(\d{1,2}/\d{1,2}/\d{4})"
    cleaned_df[['Order_No', 'Order_Date']] = cleaned_df['Description'].str.extract(order_pattern)
    cleaned_df['Order_No'] = cleaned_df['Order_No'].ffill()
    cleaned_df['Order_Date'] = pd.to_datetime(cleaned_df['Order_Date'].ffill(), errors='coerce')

    # Remove extracted information from Description
    cleaned_df['Description'] = cleaned_df['Description'].str.replace(order_pattern, '', regex=True).str.strip()

    # Remove rows with 'Order No.' in No.
    cleaned_df = cleaned_df[~cleaned_df['No.'].str.contains('Order No.', na=False)]

    # Forward fill No.
    cleaned_df['No.'] = cleaned_df['No.'].ffill()

    # Drop rows without Description
    final_df = cleaned_df.dropna(subset=['Description'], how='all')

    # Define columns for the final output
    columns = [
        'CID', 'Shipment_Date', 'Customer_Name', 'Type', 'No.',
        'Order_No', 'Order_Date', 'Description', 'Quantity', 'OutstandingQuantity',
        'Quantity on Back Order', 'Unit Price Excl. VAT',
        'Line Discount Amount', 'Inv. Discount Amount Excl. VAT', 'OutstandingOrders'
    ]

    available_columns = [col for col in columns if col in final_df.columns]
    final_df = final_df[available_columns]

    return final_df

def get_download_link(df, filename):
    """Generate a download link for a DataFrame as Excel file."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)

    b64 = base64.b64encode(output.getvalue()).decode()
    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">Download {filename}</a>'
    return href

def main():
    st.title("Excel Data Processor")

    st.markdown("""
    ### Instructions
    1. Upload your Excel file containing order data
    2. The app will clean and process the data
    3. Download the processed files (separated into Deli and FOC categories)
    """)

    # File uploader
    uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx", "xls"])

    if uploaded_file is not None:
        try:
            # Display a loading message
            with st.spinner('Processing data...'):
                # Read the Excel file
                df = pd.read_excel(uploaded_file)

                # Display the raw data (first few rows)
                st.subheader("Raw Data Preview")
                st.dataframe(df.head())

                # Clean the data
                cleaned_df = clean_data(df)

                # Split the cleaned data based on Customer_Name
                spp_deli_df = cleaned_df[cleaned_df['Customer_Name'].str.endswith('Deli', na=False)]
                spp_foc_df = cleaned_df[~cleaned_df['Customer_Name'].str.endswith('Deli', na=False)]

                # Generate timestamps for filenames
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                deli_filename = f"SPP_Deli_{timestamp}.xlsx"
                foc_filename = f"SPP_FOC_{timestamp}.xlsx"

                # Create tabs for the two different datasets
                tab1, tab2 = st.tabs(["Deli Data", "FOC Data"])

                with tab1:
                    st.subheader("Deli Data Preview")
                    st.dataframe(spp_deli_df.head())
                    st.markdown(get_download_link(spp_deli_df, deli_filename), unsafe_allow_html=True)

                    # Show stats for Deli data
                    st.subheader("Deli Data Statistics")
                    st.write(f"Total Records: {len(spp_deli_df)}")
                    if 'Quantity' in spp_deli_df.columns:
                        st.write(f"Total Quantity: {spp_deli_df['Quantity'].sum()}")

                with tab2:
                    st.subheader("FOC Data Preview")
                    st.dataframe(spp_foc_df.head())
                    st.markdown(get_download_link(spp_foc_df, foc_filename), unsafe_allow_html=True)

                    # Show stats for FOC data
                    st.subheader("FOC Data Statistics")
                    st.write(f"Total Records: {len(spp_foc_df)}")
                    if 'Quantity' in spp_foc_df.columns:
                        st.write(f"Total Quantity: {spp_foc_df['Quantity'].sum()}")

                # Provide a summary of the processing
                st.success(f"Processing complete! Found {len(spp_deli_df)} Deli records and {len(spp_foc_df)} FOC records.")

        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            st.info("Please make sure your Excel file has the expected format with the required columns.")

    # Add information about the app
    with st.expander("About this app"):
        st.markdown("""
        ### Excel Data Processor

        This application helps you clean and process Excel data files for order management.

        **Features:**
        - Extracts customer information, order numbers, and dates
        - Cleans and formats the data
        - Separates records into Deli and FOC categories
        - Provides downloadable Excel files for further use

        For support or issues, please contact your system administrator.
        """)

if __name__ == "__main__":
    main()