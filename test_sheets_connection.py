import gspread
from google.oauth2.service_account import Credentials

# Path to your downloaded JSON credentials file
SERVICE_ACCOUNT_FILE = 'C:/Users/SAGA/Desktop/Json file data alert project imp/sheets-access-1234567890.json'

# Define the required scopes
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# Authenticate with Google Sheets API using service account
creds = Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=SCOPES
)
client = gspread.authorize(creds)

# Open the Google Sheet by name
sheet = client.open("Competitor Price Monitor").sheet1  # First worksheet/tab

# ✅ Read all records as list of dictionaries
data = sheet.get_all_records()
print("Sheet Data:", data)

# ✅ Example: Read a specific cell
cell_value = sheet.cell(2, 1).value  # Row 2, Column 1
print("Cell A2 value:", cell_value)

# ✅ Example: Append a new row
new_row = ["Sadnya", "Data Analyst", "OpenAI"]
sheet.append_row(new_row)
print("New row appended.")

# ✅ Example: Update a specific cell
sheet.update('B2', 'Updated Role')
print("Cell B2 updated.")
