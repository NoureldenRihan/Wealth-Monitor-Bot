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
from PIL import Image
import io

# Ensure Tesseract is in PATH or set it here if needed (usually fine in GH Actions)
# pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract' 

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

import base64

def get_price_from_base64(base64_string, idx):
    try:
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        
        image_data = base64.b64decode(base64_string)
        image = Image.open(io.BytesIO(image_data))
        
        # Configure Tesseract
        text = pytesseract.image_to_string(image, config='--psm 7 -c tessedit_char_whitelist=0123456789.')
        extracted_value = extractNumbers(text)
        
        # Save image for debug
        filename = f"ocr_img_{idx}_val_{extracted_value}.png"
        image.save(filename)
        print(f"DEBUG: Saved image to {filename}")
        
        print(f"DEBUG: OCR on base64 image {idx} result: '{text.strip()}'")
        return float(extracted_value) if extracted_value else 0.0
    except Exception as e:
        print(f"DEBUG: Error processing base64 image {idx}: {e}")
        return 0.0

def fetchData(url, storage, normal):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        print(f"Navigating to {url}...")
        driver.get(url)
        
        # Wait for page/images to load
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "a")) # Generic wait
        )
        
        # Initialize values
        k24 = 0
        k22 = 0
        k21 = 0
        k18 = 0
        usd = 0
        
        try:
            # Find all price images
            images = driver.find_elements(By.CSS_SELECTOR, "img.price-cell")
            
            if len(images) > 0:
                print(f"DEBUG: Found {len(images)} price images.")
                
                # Extract srcs
                srcs = [img.get_attribute('src') for img in images]
                
                # DEBUG: Process all to see what we get
                values = []
                for i, src in enumerate(srcs):
                    val = get_price_from_base64(src, i)
                    values.append(val)
                    print(f"DEBUG: Image {i}: {val}")
                
                if len(values) >= 10:
                    k24 = values[1]
                    k22 = values[3]
                    k21 = values[6]
                    k18 = values[9]
                    
                    if len(values) > 12:
                         usd = values[-3]
            else:
                print("DEBUG: No images with class 'price-cell' found.")
                
        except Exception as e:
            print(f"DEBUG: Base64 extraction failed: {e}")

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

# We keep the "if True" trigger for testing as requested by user previously
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
