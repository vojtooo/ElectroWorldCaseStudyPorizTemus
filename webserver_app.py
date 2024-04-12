from flask import Flask, render_template
import pandas as pd
from sqlalchemy import create_engine, inspect, MetaData, Table, Column, Integer, String, DateTime, Float
import config_ as c
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import datetime as dt
from apscheduler.schedulers.background import BackgroundScheduler

# Create Flask app
app = Flask(__name__)

# Create a SQLAlchemy engine
engine = create_engine(c.DATABASE_PATH)

# Initialize the scheduler
scheduler = BackgroundScheduler()
scheduler.start()

def start_db():
    # Create an inspector object
    inspector = inspect(engine)
    # List all table names in the database
    table_names = inspector.get_table_names()
    # Define metadata
    metadata = MetaData()
    # Check if both tables exist
    if 'product_history_table_increment' not in table_names:
        # Define your tables
        table1 = Table(
            'product_history_table_increment',
            metadata,
            Column('ID', Integer, primary_key=True),
            Column('Subcategory', String),
            Column('Item', String),
            Column('Our Stock Status', String),
            Column('Our Sale Price', Float),
            Column('Lowest Sale Price Vendor', String),
            Column('Lowest Sale Price', Float),
            Column('Our Sale Price Excess', Float),
            Column('Lowest Total Cost', Float),
            Column('Lowest Total Cost Vendor', String),
            Column('Our Total Cost Excess', Float),
            Column('DateTime', DateTime)
        )
    if 'vendor_history_table_increment' not in table_names:
     table2 = Table(
         'vendor_history_table_increment',
         metadata,
         Column('ID', Integer, primary_key=True),
         Column('Vendor', String),
         Column('Bayesian Average', Float),
         Column('DateTime', DateTime)
     )
     # Create all tables in the database
     metadata.create_all(engine)

     print("INFO: Database initialized.")

def update_tables():
    # Data ingestion
    product_data_pd = pd.read_html(c.PRODUCT_DATA_URL, index_col="Unnamed: 0")[0]
    product_data_pd['Item'] = product_data_pd['Item'].astype("string")
    product_data_pd['Category'] = product_data_pd['Category'].astype("string")
    product_data_pd['Vendor'] = product_data_pd['Vendor'].astype("string")
    product_data_pd['Sale Price'] = pd.to_numeric(product_data_pd['Sale Price'], errors="raise")
    product_data_pd['Stock Status'] = product_data_pd['Stock Status'].astype("string")
    product_data_pd['Subcategory'] = product_data_pd['Item'].str.extract(r'([a-zA-Z\s]+)', expand=False).str.strip()

    vendor_data_pd = pd.read_html(c.VENDOR_DATA_URL, index_col="Unnamed: 0")[0]
    vendor_data_pd['Vendor Name'] = vendor_data_pd['Vendor Name'].astype("string")
    vendor_data_pd['Shipping Cost'] = pd.to_numeric(vendor_data_pd['Shipping Cost'], errors="raise")
    vendor_data_pd['Customer Review Score'] = pd.to_numeric(vendor_data_pd['Customer Review Score'], errors="raise")
    vendor_data_pd['Number of Feedbacks'] = pd.to_numeric(vendor_data_pd['Number of Feedbacks'], errors="raise")
    vendor_data_pd.rename(columns={"Vendor Name": "Vendor"}, inplace=True)

    C = vendor_data_pd["Customer Review Score"].mean()
    m = 100
    vendor_data_pd["Bayesian Average"] = (vendor_data_pd["Number of Feedbacks"]/(vendor_data_pd["Number of Feedbacks"]+m))*vendor_data_pd["Customer Review Score"] + (m/(vendor_data_pd["Number of Feedbacks"]+m))*C
    vendor_history_table_increment = vendor_data_pd[["Vendor", "Bayesian Average"]]
    vendor_history_table_increment["DateTime"] = pd.Timestamp("now", tz=dt.timezone.utc)

    product_history_table_increment = product_data_pd[product_data_pd["Vendor"] == c.MY_VENDOR_NAME][["Subcategory", "Item", "Stock Status", "Sale Price"]].reset_index()
    product_history_table_increment.rename(columns={"Stock Status" : "Our Stock Status", "Sale Price" : "Our Sale Price"}, inplace=True)

    # Add lowest price
    tmp_table = product_data_pd.loc[product_data_pd.groupby('Item')["Sale Price"].idxmin()][["Item", "Vendor", "Sale Price"]]
    tmp_table.rename(columns={"Sale Price": "Lowest Sale Price", "Vendor": "Lowest Sale Price Vendor"}, inplace=True)
    product_history_table_increment = product_history_table_increment.merge(tmp_table, on="Item", how="left")
    product_history_table_increment["Our Sale Price Excess"] = product_history_table_increment["Our Sale Price"] - product_history_table_increment["Lowest Sale Price"]

    # Add lowest total cost
    product_data_pd = product_data_pd.merge(vendor_data_pd[["Vendor", "Shipping Cost"]], on="Vendor", how="left")
    product_data_pd["Total Cost"] = product_data_pd["Sale Price"] + product_data_pd["Shipping Cost"]
    tmp_table_2 = product_data_pd.loc[product_data_pd.groupby('Item')["Total Cost"].idxmin()][["Item", "Total Cost", "Vendor"]]
    tmp_table_2.rename(columns={"Total Cost": "Lowest Total Cost", "Vendor": "Lowest Total Cost Vendor"}, inplace=True)
    product_history_table_increment = product_history_table_increment.merge(tmp_table_2, on="Item", how="left")
    product_history_table_increment["Our Total Cost Excess"] = product_history_table_increment["Our Sale Price"] + vendor_data_pd[vendor_data_pd["Vendor"]=="ElectroWorld"]["Shipping Cost"].item() - product_history_table_increment["Lowest Total Cost"]
    product_history_table_increment["DateTime"] = pd.Timestamp("now", tz=dt.timezone.utc)
    product_history_table_increment.drop(columns=["index"], inplace=True)

    # Store dfs in the database
    product_history_table_increment.to_sql('product_history_table_increment', con=engine, if_exists='replace', index=False)
    vendor_history_table_increment.to_sql('vendor_history_table_increment', con=engine, if_exists='append', index=False)
    print("INFO: Database updated.")

def before_start():
    start_db()
    update_tables()
    scheduler.add_job(update_tables, 'interval', minutes=1)  # Run my_task every minute

# Define a route to display the HTML table
@app.route('/')
def display_tables():
    product_history_table = pd.read_sql_table('product_history_table_increment', engine)
    vendor_history_table = pd.read_sql_table('vendor_history_table_increment', engine)

    df1 = pd.DataFrame(product_history_table[product_history_table["Lowest Sale Price Vendor"] != c.MY_VENDOR_NAME].groupby(["Subcategory"])["Our Sale Price Excess"].count().sort_values(ascending=False))
    df2 = pd.DataFrame(product_history_table[product_history_table["Lowest Sale Price Vendor"] != c.MY_VENDOR_NAME][["Subcategory", "Item", "Our Sale Price", "Lowest Sale Price", "Lowest Sale Price Vendor", "Our Sale Price Excess", "Our Total Cost Excess"]].sort_values("Our Sale Price Excess", ascending=False))
    df3 = pd.DataFrame(product_history_table[["Item", "Our Stock Status", "Subcategory"]].groupby(["Subcategory", "Our Stock Status"]).count())
    df4 = pd.DataFrame(product_history_table[["Item", "Our Stock Status"]].sort_values(by=["Our Stock Status"], ascending=False))
    image_path = "./static/vendor_review.png"
    # vendor_history_table[vendor_history_table["Vendor"] == c.MY_VENDOR_NAME].set_index("DateTime").sort_values("DateTime").plot(kind="bar")

    # Create a line plot for each vendor
    fig, ax = plt.subplots(figsize=(10, 5))
    for vendor, group in vendor_history_table.groupby('Vendor'):
        ax.plot(group['DateTime'], group['Bayesian Average'], marker="o", label=vendor)

    # Set labels and title
    ax.set_xlabel('DateTime')
    ax.set_ylabel('Bayesian Average')
    ax.set_title('Bayesian Average of Vendors')
    ax.legend(loc='center left', bbox_to_anchor=(1, 0.5))
    date_format = mdates.DateFormatter('%Y-%m-%d %H:%M:%S')
    ax.xaxis.set_major_formatter(date_format)
    # Rotate x-axis labels for better readability
    plt.xticks(rotation=90)
    # Show plot
    plt.tight_layout()
    plt.savefig(image_path)

    # Sort the DataFrame based on 'TimeStamp' column in descending order
    if len(vendor_history_table) > 0:
        newest_timestamp_str = vendor_history_table.sort_values(by='DateTime', ascending=False).iloc[0]['DateTime'].strftime('%Y-%m-%d %H:%M:%S')
    else:
        newest_timestamp_str = "not yet updated"

    return render_template('dashboard_template.html', df1=df1.to_html(), df2=df2.to_html(), df3=df3.to_html(), df4=df4.to_html(), image_path="vendor_review.png", newest_timestamp_str=newest_timestamp_str)

# push context manually to app
with app.app_context():
    before_start()

if __name__ == '__main__':
    app.run()
