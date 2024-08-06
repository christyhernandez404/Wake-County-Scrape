import time
import pandas as pd
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
import requests
import os
import json

# Read proxies from file
with open("valid_proxies.txt", 'r') as f:
    proxies = f.read().split('\n')

# Read the filtered data from filtered_output.json
with open('output_knightdale.json', 'r') as f:
    filtered_data = json.load(f)

url = 'https://services.wake.gov/realestate/'

options = webdriver.ChromeOptions()


# Create an empty DataFrame to store data
df_extracted = pd.DataFrame()

for index, address_data in enumerate(filtered_data):
    #  empty lists to store data for each address
    city_list = []
    zoning_list = []
    pkg_sale_date_list = []
    pkg_sale_price_list = []
    property_owner_list = []
    owner_mailing_address_list = []
    property_location_address_list = []
    total_value_assessed_list = []

    # Rotate proxies
    proxy = proxies[index % len(proxies)]
    print(f"Using the proxy: {proxy}")

    # Use proxy for requests
    proxy_dict = {"http": proxy, "https": proxy}

    # Perform the request using the rotating proxy
    try:
        res = requests.get(url, proxies=proxy_dict)
        res.raise_for_status()
    except requests.exceptions.RequestException as e:
        print("Error occurred while making the request:", e)
        continue

    # Initialize the Chrome WebDriver with the options
    driver = webdriver.Chrome(options=options)

    street_number = address_data['number']
    street_name = address_data['street']

    driver.get(url)

    try:
        # Find street number and street name fields by name
        stnum_field = driver.find_element(By.NAME, 'stnum')
        time.sleep(2)
        stnum_field.clear()
        stnum_field.send_keys(street_number)
        time.sleep(3)

        stnam_field = driver.find_element(
            By.XPATH, "//input[@name='stname'][1]")
        time.sleep(2)
        stnam_field.clear()
        stnam_field.send_keys(street_name)
        time.sleep(3)

        driver.find_element(By.NAME, "Search by Address").click()
        time.sleep(5)

        # Click on the link to view property details
        driver.find_element(
            By.XPATH, '/html/body/table[2]/tbody/tr/td/table/tbody/tr[2]/td[2]/b/a/font').click()
        time.sleep(5)

        tbody = driver.find_element(By.XPATH, "/html/body/table[2]")
        tbody2 = driver.find_element(By.XPATH, "/html/body/table[3]")

        data1 = []
        data2 = []

        for tr in tbody.find_elements(By.XPATH, '//tr'):
            row = [item.text for item in tr.find_elements(By.XPATH, './td')]
            data1.append(row)

        for tr in tbody2.find_elements(By.XPATH, '//tr'):
            row = [item.text for item in tr.find_elements(By.XPATH, './td')]
            data2.append(row)

        # Find City and its value in data1
        city_data = None
        for row in data1:
            if row[0] == 'City':
                city_data = row
                break

        # Find Zoning and its value in data1
        zoning_data = None
        for row in data1:
            if row[0] == 'Zoning':
                zoning_data = row
                break

        # Find Pkg Sale Date and its value in data1
        pkg_sale_date_data = None
        for row in data1:
            if row[0] == 'Pkg Sale Date':
                pkg_sale_date_data = row
                break

        # Find Pkg Sale Price and its value in data1
        pkg_sale_price_data = None
        for row in data1:
            if row[0] == 'Pkg Sale Price':
                pkg_sale_price_data = row
                break

        # Find Property Owner title in data1
        for i, row in enumerate(data1):
            if row[0] == 'Property Owner':
                # Check if the next row exists
                if i < len(data1) - 1:
                    property_owner_data = data1[i+1]
                    break

        # Find Owner's Mailing Address and its value in data1
        owner_mailing_address_data = None
        for f, row in enumerate(data1):
            if row[0] == "Owner's Mailing Address":
                # Check if the next row exists
                if f < len(data1) - 1:
                    owner_mailing_address_data = data1[f+1]
                    break

        property_location_address_data = None
        for n, row in enumerate(data1):
            if row[0] == 'Property Location Address':
                # Check if the next row exists
                if n < len(data1) - 1:
                    property_location_address_data = data1[n+1]
                    break

        total_value_assessed_data = None
        for row in data1:
            if row[0] == 'Total Value Assessed*':
                total_value_assessed_data = row
                break

        # Append data to lists
        city_list.append(city_data[1] if city_data else None)
        zoning_list.append(zoning_data[1] if zoning_data else None)
        pkg_sale_date_list.append(
            pkg_sale_date_data[1] if pkg_sale_date_data else None)
        pkg_sale_price_list.append(
            pkg_sale_price_data[1] if pkg_sale_price_data else None)
        property_owner_list.append(
            property_owner_data[0] if property_owner_data else None)
        owner_mailing_address_list.append(
            owner_mailing_address_data[0] if owner_mailing_address_data else None)
        property_location_address_list.append(
            property_location_address_data[0] if property_location_address_data else None)
        total_value_assessed_list.append(
            total_value_assessed_data[1] if total_value_assessed_data else None)

    except NoSuchElementException as e:
        print(
            f"Error occurred while processing address: {street_number} {street_name}")

        print(e)
        continue

    finally:
        # Close the browser
        driver.quit()

    # Create a DataFrame from the extracted data
    data = {
        'City': city_list,
        'Zoning': zoning_list,
        'Pkg Sale Date': pkg_sale_date_list,
        'Pkg Sale Price': pkg_sale_price_list,
        'Property Owner': property_owner_list,
        "Owner's Mailing Address": owner_mailing_address_list,
        'Property Location Address': property_location_address_list,
        'Total Value Assessed*': total_value_assessed_list
    }

    df_data = pd.DataFrame(data)

    # Append data to CSV file
    df_data.to_csv('knightdale_data.csv', index=False, mode='a',
                   header=not os.path.exists('knightdale_data.csv'))
