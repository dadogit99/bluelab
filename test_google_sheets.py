
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Step 1: Define the scope and credentials file
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("gcreds.json", scope)

# Step 2: Authorize client
client = gspread.authorize(creds)

# Step 3: Open the sheet by name
spreadsheet = client.open("Edenic Telemetry Log")  # Make sure this name matches your Google Sheet
worksheet = spreadsheet.worksheet("Sheet1")        # Adjust if your sheet tab has a different name

# Step 4: Append a test row
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
test_row = [now, "TEST_PH", "TEST_EC", "TEST_TEMP_F"]
worksheet.append_row(test_row)

print("✅ Successfully wrote test row to Google Sheet.")
