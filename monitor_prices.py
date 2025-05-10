import re
import time
from datetime import datetime
import mysql.connector
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
import smtplib
from email.mime.text import MIMEText
import os

# === Email Alert Function ===
def send_email_alert(product_name, our_price, ebay_price, new_price):
    sender_email = os.environ['ALERT_SENDER_EMAIL']
    receiver_email = os.environ['ALERT_RECEIVER_EMAIL']
    app_password = os.environ['ALERT_APP_PASSWORD']

    subject = f"Price Drop Alert: {product_name}"
    body = f"""
    Product: {product_name}
    Our Price: ₹{our_price}
    eBay Price: ₹{ebay_price}
    New Updated Price: ₹{new_price}

    Action Taken: Our price has been updated and logged.
    """

    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = receiver_email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(sender_email, app_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        print("   📧 Email alert sent.")
    except Exception as e:
        print(f"   ❌ Failed to send email: {e}")

# === Setup Selenium ===
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# === Use environment variables for database credentials ===
db = mysql.connector.connect(
    host=os.environ['DB_HOST'],
    port=int(os.environ['DB_PORT']),
    user=os.environ['DB_USER'],
    password=os.environ['DB_PASSWORD'],
    database=os.environ['DB_NAME']
)
cursor = db.cursor()

# === Function: Scrape eBay Price ===
def get_ebay_price(url):
    try:
        driver.get(url)
        time.sleep(3)
        price_text = None
        price_elems = driver.find_elements(By.XPATH, "//span[contains(text(), '$') or contains(text(), '₹')]")
        for elem in price_elems:
            text = elem.text.strip()
            if re.search(r"\d+\.\d{2}", text):
                price_text = text
                break
        if not price_text:
            try:
                fallback_elem = driver.find_element(By.CLASS_NAME, "x-price-whole")
                price_text = fallback_elem.text.strip()
            except:
                return None
        match = re.search(r"\d+(?:\.\d+)?", price_text.replace(",", ""))
        if match:
            return float(match.group())
        else:
            return None
    except (NoSuchElementException, TimeoutException, ValueError):
        return None

# === Load Products from DB ===
cursor.execute("SELECT product_id, product_name, our_price, ebay_url FROM products")
products = cursor.fetchall()

for product in products:
    product_id, product_name, our_price, ebay_url = product
    print(f"\n🔍 Checking: {product_name} (ID: {product_id})")
    print(f"   Our Price: ₹{our_price}")

    ebay_price = get_ebay_price(ebay_url)
    if ebay_price is None:
        print("   ❌ Could not fetch price.")
        continue

    print(f"   eBay Price: ₹{ebay_price}")
    if ebay_price < our_price:
        price_diff_percent = ((our_price - ebay_price) / our_price) * 100
        if price_diff_percent > 10:
            new_price = round(ebay_price - 5, 2)  # Subtract margin
            print(f"   🔁 Updating our price to ₹{new_price}")

            # Update product price
            cursor.execute("UPDATE products SET our_price = %s WHERE product_id = %s", (new_price, product_id))
            db.commit()

            # Log the price change
            cursor.execute("""
                INSERT INTO price_change_log (product_id, old_price, new_price, ebay_price, updated_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (product_id, our_price, new_price, ebay_price, datetime.now()))
            db.commit()

            # Send email alert
            send_email_alert(product_name, our_price, ebay_price, new_price)
        else:
            print("   ⚠️  Minor difference, no update made.")
    else:
        print("   ✅ Our price is competitive.")

# === Cleanup ===
driver.quit()
cursor.close()
db.close()

# import re
# import time
# from datetime import datetime
# import mysql.connector
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# from selenium.webdriver.common.by import By
# from selenium.common.exceptions import TimeoutException, NoSuchElementException
# from webdriver_manager.chrome import ChromeDriverManager
# import os

# # === Setup Selenium ===
# options = webdriver.ChromeOptions()
# options.add_argument("--headless")
# options.add_argument("--disable-gpu")
# options.add_argument("--no-sandbox")
# driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

# # === Use environment variables for database credentials ===
# db = mysql.connector.connect(
#     host=os.environ['DB_HOST'],
#     port=int(os.environ['DB_PORT']),
#     user=os.environ['DB_USER'],
#     password=os.environ['DB_PASSWORD'],
#     database=os.environ['DB_NAME']
# )
# cursor = db.cursor()

# # === Function: Scrape eBay Price ===
# def get_ebay_price(url):
#     try:
#         driver.get(url)
#         time.sleep(3)
#         price_text = None
#         price_elems = driver.find_elements(By.XPATH, "//span[contains(text(), '$') or contains(text(), '₹')]")
#         for elem in price_elems:
#             text = elem.text.strip()
#             if re.search(r"\d+\.\d{2}", text):
#                 price_text = text
#                 break
#         if not price_text:
#             try:
#                 fallback_elem = driver.find_element(By.CLASS_NAME, "x-price-whole")
#                 price_text = fallback_elem.text.strip()
#             except:
#                 return None
#         match = re.search(r"\d+(?:\.\d+)?", price_text.replace(",", ""))
#         if match:
#             return float(match.group())
#         else:
#             return None
#     except (NoSuchElementException, TimeoutException, ValueError):
#         return None

# # === Load Products from DB ===
# cursor.execute("SELECT product_id, product_name, our_price, ebay_url FROM products")
# products = cursor.fetchall()

# for product in products:
#     product_id, product_name, our_price, ebay_url = product
#     print(f"\n🔍 Checking: {product_name} (ID: {product_id})")
#     print(f"   Our Price: ₹{our_price}")
    
#     ebay_price = get_ebay_price(ebay_url)
#     if ebay_price is None:
#         print("   ❌ Could not fetch price.")
#         continue

#     print(f"   eBay Price: ₹{ebay_price}")
#     if ebay_price < our_price:
#         new_price = round(ebay_price - 5, 2)  # Subtract margin
#         print(f"   🔁 Updating our price to ₹{new_price}")

#         # Update product price
#         cursor.execute("UPDATE products SET our_price = %s WHERE product_id = %s", (new_price, product_id))
#         db.commit()

#         # Log the price change
#         cursor.execute("""
#             INSERT INTO price_change_log (product_id, old_price, new_price, ebay_price, updated_at)
#             VALUES (%s, %s, %s, %s, %s)
#         """, (product_id, our_price, new_price, ebay_price, datetime.now()))
#         db.commit()
#     else:
#         print("   ✅ Our price is competitive.")

# # === Cleanup ===
# driver.quit()
# cursor.close()
# db.close()
