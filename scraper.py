#!/usr/bin/python3
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import argparse
import os
import time
import random

def get_vpn_apps():
    # Define the URL for the search page
    url = "https://en.uptodown.com/android/search"
    max_retries = 5
    retries = 0
    user_agent = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }
    payload = {'q': 'vpn'}

    # Try to get a response, retrying if rate limited
    while retries < max_retries:
        response = requests.post(url, data=payload, headers=user_agent)
        if response.status_code == 200:
            break
        elif response.status_code == 429:
            # Handle rate limiting by waiting before retrying
            delay = 2 ** retries + random.uniform(0, 1)
            print(f"Rate limit hit. Retrying in {delay:.2f} seconds...")
            time.sleep(delay)
            retries += 1
        else:
            print(f"Failed to retrieve data. Status code: {response.status_code}")
            return []
    
    if retries == max_retries:
        print(f"Max retries reached. Skipping...")
        return []

    print(f"Response status code: {response.status_code}")

    # Parse the response HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    apps = []
    # Find all figure elements which contain the app details
    for figure in soup.find_all('figure'):
        onclick_attr = figure.get('onclick', '')
        if "location.href='" in onclick_attr:
            app_url = onclick_attr.split("location.href='")[1].split("';")[0]
            print(f"Found URL: {app_url}")
            content = get_app_package_name(app_url)
            apps.append(content)
            if len(apps) >= 30:
                break
    
    print(f"Retrieved {len(apps)} apps")
    return apps

def get_app_package_name(app_url):
    max_retries = 5
    retries = 0
    user_agent = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
    }

    # Try to get the app page, retrying if rate limited
    while retries < max_retries:
        response = requests.get(app_url, headers=user_agent)
        if response.status_code == 200:
            with open("output.html", "a") as file:
                file.write(response.text)
            # Parse the app page HTML
            soup = BeautifulSoup(response.text, 'html5lib')
            # Find all table rows with the class 'full'
            rows = soup.find_all('tr', class_='full')
            for row in rows:
                cells = row.find_all('td')
                stop = False
                for cell in cells:
                    if stop:
                        package_name = cell.get_text(strip=True)
                        print(f"Package Name: {package_name}")
                        return package_name
                    if "Package Name" in cell.get_text(strip=True):
                        stop = True
            print("Package name not found in the HTML content.")
            return None
        elif response.status_code == 429:
            # Handle rate limiting by waiting before retrying
            delay = 2 ** retries + random.uniform(0, 1)
            print(f"Rate limit hit for {app_url}. Retrying in {delay:.2f} seconds...")
            time.sleep(delay)
            retries += 1
        else:
            print(f"Failed to retrieve app page. Status code: {response.status_code}")
            return None

    print(f"Max retries reached for {app_url}. Skipping...")
    return None

def main(args):
    opt = args.option
    today = datetime.today()
    formatted_date = today.strftime("%m_%d_%Y")

    if opt == 'top_apps':
        df = pd.DataFrame()

        # Adding a random initial delay to avoid burst behavior
        initial_delay = random.uniform(5, 15)
        print(f"Initial delay of {initial_delay:.2f} seconds...")
        time.sleep(initial_delay)

        # Retrieve VPN apps
        apps = get_vpn_apps()

        if len(apps) < 30:
            print(f"Not enough apps found")
        else:
            # Save the retrieved apps to a CSV file
            df = pd.DataFrame(apps, columns=['url'])
            os.makedirs('data/apps', exist_ok=True)
            df.to_csv(f'data/apps/{formatted_date}.csv', index=False, sep='\t')
            print(f"Saved data to data/apps/{formatted_date}.csv")
    
    elif opt == 'read':
        # Read data from the specified date
        read_data(args.date)

def read_data(date):
    file_path = f"data/apps/{date}.csv"
    if not os.path.exists(file_path):
        print(f"Error: The CSV file for {date} does not exist.")
        return

    # Read and print the data from the CSV file
    df = pd.read_csv(file_path, sep='\t')
    print(df)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Script to record Top VPN apps from Uptodown')

    parser.add_argument('--option', type=str, required=True, choices=['top_apps', 'read'], help='top_apps: Top VPN apps, read: Read saved apps data')
    args = parser.parse_args()

    if args.option == "read":
        parser.add_argument('--date', required=True, help='Specify date in mm_dd_yyyy format')
        args = parser.parse_args()

    main(args)
