from io import BytesIO
from pickletools import optimize
import sqlite3
import pdfkit as pdf
import os
import sys
import datetime
import streamlit as st
import pandas as pd
from PIL import Image

conn = sqlite3.connect('dsa.db')
c = conn.cursor()

def create_table():
    sql_create_table = """
    CREATE TABLE IF NOT EXISTS dsa(id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
    ds_number INTEGER NOT NULL UNIQUE,
    customer TEXT NOT NULL,
    equipment INTEGER NULL,
    serial_number INTEGER NOT NULL, 
    process_date TEXT NOT NULL,
    delivery_date TEXT NOT NULL,
    upload_date TEXT NOT NULL,
    description TEXT,
    photo BLOB NOT NULL)
    """
    c.execute(sql_create_table)

def add_data(ds_number,customer, equipment, serial_number, process_date, delivery_date, upload_date, description, photo):
    sql_insert = """
    INSERT INTO dsa(id, ds_number, customer, equipment, serial_number, process_date, delivery_date, upload_date, description, photo)
     VALUES (null, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    c.execute(sql_insert, (ds_number, customer, equipment, serial_number, process_date, delivery_date, upload_date, description, photo))
    conn.commit()

def get_ds(query):
    c.execute(query)
    data = c.fetchall()
    return data

def writeToFile(data, filename):
    if not os.path.exists('photo'):
        os.makedirs('photo')
    with open(filename,'wb') as file:
        del_older_files('photo')
        file.write(data)

def convert_df(df):
    headerreport="""
    <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        .dataframe {
            margin-left: auto;
            margin-right: auto;            
        }

        h1, h2 { text-align: center;}

        table { 
            border-collapse: collapse;            
        }

        tr:nth-child(even){background-color: azure;}     
        
        th, td { padding: 5px;}
        
        th:nth-child(1) {display: none;}
    </style>
    <title>DSA-Report</title>
</head>
<body>
    <h1>PT Astra Graphia</h1>
    <h2>Rekap Delivery Archive</h2>
"""

    footerReport="""
</body>
</html>
"""
    df.to_html('data.html')

    fo=open('data.html', 'r')
    data = fo.read()
    fo.close()
    
    fw=open('container.html', 'w')
    fw.write(headerreport)
    fw.write(data)
    fw.write(footerReport)
    fw.close()

    pdf.from_file('container.html', 'report.pdf')

def del_older_files(req_path):
    N=7
    if not os.path.exists(req_path):
        sys.exit(1)
    if os.path.isfile(req_path):
        sys.exit(2)
    today = datetime.datetime.now()
    for each_file in os.listdir(req_path):
        each_file_path = os.path.join(req_path,each_file)
        if os.path.isfile(each_file_path):
            file_cre_date = datetime.datetime.fromtimestamp(os.path.getctime(each_file_path))
            dif_days = (today - file_cre_date).days
            if dif_days > N :
                os.remove(each_file_path)

def main():
    html_temp = """
    <div style="background-color:{}; padding: 9px; border-radius:0px">
    <h1 style="color: {}; text-align: center;">PT ASTRAGRAPHIA</h1>
    </div>
    """
    st.markdown(html_temp.format('royalblue', 'white'), unsafe_allow_html=True)
    html_temp = """
    <div style="background-color:{}; padding: 0px; border-radius:0px">
    <h3 style="color: {}; text-align: center;">DELIVERY SLIP ARCHIVE</h3>
    </div>
    """
    st.markdown(html_temp.format('royalblue', 'white'), unsafe_allow_html=True)


    menu = ["Upload DS", "Search DS", "Rekap DS"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Search DS":
        st.subheader("Search Delivery Slip")
        search = st.text_input("Enter keyword")
        search_choice = st.radio("Field to Search", ("DS Number", "Customer Name", "Equipment", "Serial Number"))
        if st.button('Search'):
            if search_choice == "DS Number":
                query = 'SELECT * FROM dsa WHERE ds_number="' + search + '"'
            elif search_choice == "Customer Name":
                query = 'SELECT * FROM dsa WHERE customer LIKE \'%' + search + '%\''
            elif search_choice == "Equipment":
                query = 'SELECT * FROM dsa WHERE equipment="' + search + '"'
            elif search_choice == "Serial Number":
                query = 'SELECT * FROM dsa WHERE serial_number="' + search + '"'

            ds_result = get_ds(query)

            for i in ds_result:
                st.text("Delivery Slip Number : {}".format(i[1]))
                st.text("Customer Name : {}".format(i[2]))
                st.text("Equipment Number: {}".format(i[3]))
                st.text("Serial Number : {}".format(i[4]))
                st.text("Process Date : {}".format(i[5]))
                st.text("Delivery Date : {}".format(i[6]))
                st.text("Upload Time : {}".format(i[7]))
                st.text("Description : {}".format(i[8]))
                pfname = ("{}.jpg".format(i[1]))
                photo_path = os.path.join('photo', pfname)
                writeToFile(i[9], photo_path)
                image = Image.open(photo_path)
                st.image(image)

    elif choice == "Upload DS":
        st.subheader("Upload DS")
        create_table()
        ds_number = st.text_input('DS Number')
        customer = st.text_input('Customer Name')
        equipment = st.text_input('Equipment Number')
        serial_number = st.text_input('Serial Number')
        process_date = st.date_input('Process Date')
        delivery_date = st.date_input('Delivery Date')
        upload_date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        description = st.text_area('Description')
        photo = st.file_uploader(label="Select DS photo", type=['jpg'])
        if st.button("Add"):
            with BytesIO() as output:
                with Image.open(photo) as img:
                    img.save(output, 'JPEG', optimize=True, quality=10)
                bytes_data = output.getvalue()
            add_data(ds_number, customer, equipment, serial_number, process_date, delivery_date, upload_date, description, bytes_data)
            st.success("Deliver Slip :'{}' saved".format(ds_number))

    elif choice == "Rekap DS":
        st.subheader("Rekap DS")
        start_date = st.date_input("Start Date")
        end_date = st.date_input("End Date")
        if st.button("Display DS"):            
            query = 'SELECT ds_number AS "DS NUMBER", upload_date AS "UPLOAD DATE", customer AS "CUSTOMER NAME", serial_number AS "SERIAL NUMBER", equipment AS "EQUIPMENT" FROM dsa WHERE upload_date BETWEEN "{}" AND "{}" ORDER BY upload_date DESC'.format(start_date, end_date)
            sql_query = pd.read_sql_query(query, conn)
            df = pd.DataFrame(sql_query, columns=['DS NUMBER', 'CUSTOMER NAME', 'EQUIPMENT', 'SERIAL NUMBER', 'UPLOAD DATE'])
            st.table(df)
            reportdata = convert_df(df)
            with open('report.pdf', 'rb') as file:
                btn = st.download_button(
                    label="Download Recap",
                    data=file,
                    file_name='recap.pdf',
                    mime='application/octet-stream'
                )

if __name__ == '__main__':
    main()
