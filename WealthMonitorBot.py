from datetime import datetime, timezone
import os
import telebot
import re
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pytesseract
from PIL import Image, ImageOps
import io
import base64

def extractNumbers(string):
    # Only keep digits and dots
    return ''.join(char for char in string if char.isdigit() or char == '.')

def sendMsg(data, storage, normal):
    bot_token = os.getenv('BOT_TOKEN')
    if normal:
        chat_id = os.getenv('CHAT_ID')
    else:
        chat_id = os.getenv('CHAT_IDZ')
        
    bot = telebot.TeleBot(bot_token)
    
    message = f'''Wealth Monitor Bot (OCR Edition) is here!

GOLD:

24K: {storage["24KGold"]}g x {data["24K Egy Gold"]['weight']} = {data["24K Egy Gold"]['value']} EGP

22K: {storage["22KGold"]}g x {data["22K Egy Gold"]['weight']} = {data["22K Egy Gold"]['value']} EGP

21K: {storage["21KGold"]}g x {data["21K Egy Gold"]['weight']} = {data["21K Egy Gold"]['value']} EGP

18K: {storage["18KGold"]}g x {data["18K Egy Gold"]['weight']} = {data["18K Egy Gold"]['value']} EGP

Your Total Gold Value: {data["Your Gold Value"]} EGP

CASH:

Cash (EGP): {storage["EGPCash"]} EGP

Cash (USD): {storage['USDCash']} USD

USD to EGP: {data['USD to EGP']} EGP

Your Total Cash Value: {data["Your Cash Value"]} EGP

TOTAL:

Total Wealth (EGP): {data["Total in EGP"]} EGP

Total Wealth (USD): {data["Total in USD"]} USD

    '''
    
    bot.send_message(chat_id, message)
    print("Message Sent")

def fetchUSDGoogle(driver):
    try:
        driver.get("https://www.google.com/finance/quote/USD-EGP")
        
        # Wait for the price element
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.YMlKec.fxKbKc"))
        )
        
        rate_element = driver.find_element(By.CSS_SELECTOR, "div.YMlKec.fxKbKc")
        rate_text = rate_element.text
        
        val = float(extractNumbers(rate_text))
        return round(val, 2)
        
    except Exception as e:
        print(f"Error fetching USD: {e}")
        return 0.0

def get_price_from_base64(base64_string):
    try:
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        image_data = base64.b64decode(base64_string)
        image = Image.open(io.BytesIO(image_data))
        
        # Preprocessing
        image = ImageOps.expand(image, border=20, fill='white')
        if image.mode != 'RGB': image = image.convert('RGB')
        new_size = tuple(3 * x for x in image.size)
        image = image.resize(new_size, Image.Resampling.LANCZOS)
        
        # Configure Tesseract
        text = pytesseract.image_to_string(image, config='--psm 7 -c tessedit_char_whitelist=0123456789.')
        extracted_value = extractNumbers(text)
        
        # TRUNCATE to first 4 digits
        if extracted_value and len(extracted_value) > 4:
            extracted_value = extracted_value[:4]
            
        return float(extracted_value) if extracted_value else 0.0
    except Exception:
        return 0.0

def fetchData(url, storage, normal):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        usd = fetchUSDGoogle(driver)
        
        driver.get(url)
        
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "a"))
        )
        
        k24 = 0
        k22 = 0
        k21 = 0
        k18 = 0
        
        try:
            images = driver.find_elements(By.CSS_SELECTOR, "img.price-cell")
            
            if len(images) > 0:
                srcs = [img.get_attribute('src') for img in images]
                
                values = []
                for src in srcs:
                    val = get_price_from_base64(src)
                    values.append(val)
                
                if len(values) >= 10:
                    k24 = values[1]
                    k22 = values[3]
                    k21 = values[5]
                    k18 = values[7]
            else:
                print("No price images found.")
                
        except Exception as e:
            print(f"Extraction failed: {e}")

        # Update data object
        data['24K Egy Gold']['weight'] = round(k24)
        data['24K Egy Gold']['value'] = round(data['24K Egy Gold']['weight'] * storage['24KGold'])
        
        data['22K Egy Gold']['weight'] = round(k22)
        data['22K Egy Gold']['value'] = round(data['22K Egy Gold']['weight'] * storage['22KGold'])
        
        data['21K Egy Gold']['weight'] = round(k21)
        data['21K Egy Gold']['value'] = round(data['21K Egy Gold']['weight'] * storage['21KGold'])
        
        data['18K Egy Gold']['weight'] = round(k18)
        data['18K Egy Gold']['value'] = round(data['18K Egy Gold']['weight'] * storage['18KGold'])
        
        data['Your Gold Value'] = data["24K Egy Gold"]['value'] + data["22K Egy Gold"]['value'] + data["21K Egy Gold"]['value'] + data["18K Egy Gold"]['value']
        
        data['USD to EGP'] = usd
        data['Your Cash Value'] = round((storage['USDCash'] * data['USD to EGP']) + storage['EGPCash'])
        data['Total in EGP'] = round(storage['EGPCash'] + data['Your Gold Value'] + (storage['USDCash'] * data['USD to EGP']))
        if data['USD to EGP'] > 0:
             data['Total in USD'] = round(storage['USDCash'] + ((storage['EGPCash'] + data['Your Gold Value']) / data['USD to EGP']))
        else:
             data['Total in USD'] = 0

        sendMsg(data, storage, normal)

    except Exception as e:
        print(f"Error in fetchData: {e}")
    finally:
        driver.quit()

fixedHour = 19
url = 'https://market.isagha.com/prices'
currentHour = datetime.now(timezone.utc).hour

# if fixedHour == currentHour: 
if True: 
    # Setup Data Structures
    data = {
        '24K Egy Gold': {'weight': 0, 'value': 0},
        '22K Egy Gold': {'weight': 0, 'value': 0},
        '21K Egy Gold': {'weight': 0, 'value': 0},
        '18K Egy Gold': {'weight': 0, 'value': 0},
        'USD to EGP': 0,
        'Your Gold Value': 0,
        'Your Cash Value': 0,
        'Total in EGP': 0,
        'Total in USD': 0,
    }

    storage = {
        '24KGold': float(os.getenv('G24K') if os.getenv('G24K') else 0),
        '22KGold': float(os.getenv('G22K') if os.getenv('G22K') else 0),
        '21KGold': float(os.getenv('G21K') if os.getenv('G21K') else 0),
        '18KGold': float(os.getenv('G18K') if os.getenv('G18K') else 0),
        'EGPCash': float(os.getenv('EGP_C') if os.getenv('EGP_C') else 0),
        'USDCash': float(os.getenv('USD_C') if os.getenv('USD_C') else 0),
    }

    storageZ = {
        '24KGold': float(os.getenv('G24KZ') if os.getenv('G24KZ') else 0),
        '22KGold': float(os.getenv('G22KZ') if os.getenv('G22KZ') else 0),
        '21KGold': float(os.getenv('G21KZ') if os.getenv('G21KZ') else 0),
        '18KGold': float(os.getenv('G18KZ') if os.getenv('G18KZ') else 0),
        'EGPCash': float(os.getenv('EGP_CZ') if os.getenv('EGP_CZ') else 0),
        'USDCash': float(os.getenv('USD_CZ') if os.getenv('USD_CZ') else 0),
    }

    fetchData(url, storage, True)
    fetchData(url, storageZ, False)
else:
    print('Invalid Timing!')
