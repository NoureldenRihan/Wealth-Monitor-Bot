from bs4 import BeautifulSoup
from datetime import datetime, timezone
import requests
import os
import telebot

def extractNumbers(string):
    return ''.join(char for char in string if char.isdigit() or char == '.')[:-1]

def saveData(data):
    if normal:
        file_path = './data_log.txt'
    else:
        file_path = './data_logZ.txt'

    # Write data to the text file
    with open(file_path, 'a') as file:
        file.write(f"{datetime.now(timezone.utc)} - {data}\n")

    print("Data written to data_log.")

def sendMsg():
    bot_token = os.getenv('BOT_TOKEN')
    if normal:
        chat_id = os.getenv('CHAT_ID')
        bot = telebot.TeleBot(bot_token)
        
        message = f'''Wealth Monitor Bot is here!

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
        saveData(message)
    else: 
        chat_id = os.getenv('CHAT_IDZ')
        bot = telebot.TeleBot(bot_token)
        
        message = f'''Wealth Monitor Bot is here!

GOLD:

24K: {storageZ["24KGold"]}g x {data["24K Egy Gold"]['weight']} = {data["24K Egy Gold"]['value']} EGP

22K: {storageZ["22KGold"]}g x {data["22K Egy Gold"]['weight']} = {data["22K Egy Gold"]['value']} EGP

21K: {storageZ["21KGold"]}g x {data["21K Egy Gold"]['weight']} = {data["21K Egy Gold"]['value']} EGP

18K: {storageZ["18KGold"]}g x {data["18K Egy Gold"]['weight']} = {data["18K Egy Gold"]['value']} EGP

Your Total Gold Value: {data["Your Gold Value"]} EGP

CASH:

Cash (EGP): {storageZ["EGPCash"]} EGP

Cash (USD): {storageZ['USDCash']} USD

USD to EGP: {data['USD to EGP']} EGP

Your Total Cash Value: {data["Your Cash Value"]} EGP

TOTAL:

Total Wealth (EGP): {data["Total in EGP"]} EGP

Total Wealth (USD): {data["Total in USD"]} USD

    '''
        
        bot.send_message(chat_id, message)

        print("Message Sent")
        saveData(message)

def fetchData(url, storage):
    response = requests.get(url)
    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')

        # Website Pattern is as follows:
        # [0] buy price
        # [1] sell price
        # [2] Diffrence
        # same pattern for every Karat so each Karat has 3 Values

        # Retreive 24K Gold Price
        K24price = soup.select('div.isagha-panel > div.clearfix > div.col-xs-4 > div.value')[1].text
        data['24K Egy Gold']['weight'] = round(float(extractNumbers(K24price)))
        data['24K Egy Gold']['value'] = round(data['24K Egy Gold']['weight'] * storage['24KGold'])

        # Retreive 22K Gold Price
        K22price = soup.select('div.isagha-panel > div.clearfix > div.col-xs-4 > div.value')[3].text
        data['22K Egy Gold']['weight'] = round(float(extractNumbers(K22price)))
        data['22K Egy Gold']['value'] = round(data['22K Egy Gold']['weight'] * storage['22KGold'])

        # Retreive 21K Gold Price
        K21price = soup.select('div.isagha-panel > div.clearfix > div.col-xs-4 > div.value')[6].text
        data['21K Egy Gold']['weight'] = round(float(extractNumbers(K21price)))
        data['21K Egy Gold']['value'] = round(data['21K Egy Gold']['weight'] * storage['21KGold'])

        # Retreive 18K Gold Price
        K18price = soup.select('div.isagha-panel > div.clearfix > div.col-xs-4 > div.value')[9].text
        data['18K Egy Gold']['weight'] = round(float(extractNumbers(K18price)))
        data['18K Egy Gold']['value'] = round(data['18K Egy Gold']['weight'] * storage['18KGold'])

        # Add All Gold Values
        data['Your Gold Value'] = data["24K Egy Gold"]['value'] + data["22K Egy Gold"]['value'] + data["21K Egy Gold"]['value'] + data["18K Egy Gold"]['value']

        # Retreive USD to EGP Price
        USDPrice = soup.select('div.isagha-panel > div.clearfix > div.col-xs-4 > div.value')[-3].text
        data['USD to EGP']= float(extractNumbers(USDPrice))

        # Add All Cash Values
        data['Your Cash Value'] = round((storage['USDCash'] * data['USD to EGP']) + storage['EGPCash'])

        # calculate total wealth in EGP
        data['Total in EGP'] = round(storage['EGPCash'] + data['Your Gold Value'] + (storage['USDCash'] * data['USD to EGP']))

        # calculate total wealth in USD
        data['Total in USD'] = round(storage['USDCash'] + ((storage['EGPCash'] + data['Your Gold Value']) / data['USD to EGP']))
    else:
        print(f"Failed to retrieve the page. Status code: {response.status_code}")

    sendMsg()

fixedHour = 19 # GMT/UTC timezone

url = 'https://market.isagha.com/prices'

currentHour = datetime.now(timezone.utc).hour

normal = True

data = {
    '24K Egy Gold': {
        'weight': 0,
        'value': 0,
    },
    '22K Egy Gold': {
        'weight': 0,
        'value': 0,
    },
    '21K Egy Gold': {
        'weight': 0,
        'value': 0,
    },
    '18K Egy Gold': {
        'weight': 0,
        'value': 0,
    },
    'USD to EGP': 0,
    'Your Gold Value': 0,
    'Your Cash Value': 0,
    'Total in EGP': 0,
    'Total in USD': 0,
}

storage = {
    '24KGold': float(os.getenv('G24K')),
    '22KGold': float(os.getenv('G22K')),
    '21KGold': float(os.getenv('G21K')),
    '18KGold': float(os.getenv('G18K')),
    'EGPCash': float(os.getenv('EGP_C')),
    'USDCash': float(os.getenv('USD_C')),
}

storageZ = {
    '24KGold': float(os.getenv('G24KZ')),
    '22KGold': float(os.getenv('G22KZ')),
    '21KGold': float(os.getenv('G21KZ')),
    '18KGold': float(os.getenv('G18KZ')),
    'EGPCash': float(os.getenv('EGP_CZ')),
    'USDCash': float(os.getenv('USD_CZ')),
}

if fixedHour == currentHour:
    fetchData(url, storage)
    normal = False
    fetchData(url, storageZ)
else:
    print('Invalid Timing!')
