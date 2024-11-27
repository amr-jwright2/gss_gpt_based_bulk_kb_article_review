import os
import requests
import time
import pandas as pd
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import csv
import re
import time
from markdownify import markdownify as md
import json

load_dotenv()

CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')

url_get_retries = 3
url_get_timeout = 7

def proxy_settings(use_proxy):
    if use_proxy == True:
        return {'http': 'http://proxy-dmz.intel.com:911',
             'https': 'http://proxy-dmz.intel.com:912'}
    else:
        return None

def get_access_token(client_id, client_secret, proxy_setting):
    url = "https://apis-internal.intel.com/v1/auth/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    response = requests.post(url, data=data, headers=headers, proxies=proxy_setting)
    response_data = response.json()
    access_token = response_data['access_token']
    expires_in = response_data['expires_in']
    return access_token, time.time() + int(expires_in)

def invoke_model(access_token, system_prompt, user_content, proxy_setting):
    url = "https://apis-internal.intel.com/generativeaiinference/v1"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    data = {
        "correlationId": "string",
        "options": {
            "temperature": 0.2,
            "top_P": 0.40,
            "frequency_Penalty": 0,
            "presence_Penalty": 0,
            "max_Tokens": 1000,
            "stop": None,
            "model": "gpt-4-turbo",
            "allowModelFallback": True
        },
        "conversation": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": user_content
            }
        ]
    }
    
    response = requests.post(url, json=data, headers=headers, proxies=proxy_setting)
    response_data = response.json()
    suggestions = response_data['conversation'][2]['content']
    return suggestions

def check_token_expiry(access_token, expiry_time, client_id, client_secret):
    if time.time() >= expiry_time:
        access_token, expiry_time = get_access_token(client_id, client_secret)
    return access_token, expiry_time

def read_csv(file_path):
    df = pd.read_csv(file_path)
    urls = df['External URL'].tolist()
    return urls

def fetch_page_content(url, proxy_setting, url_retries, url_timeout):

    for retry in range(url_retries):
        try:
            response = requests.get(url, proxies=proxy_setting, timeout=url_timeout)
            response.raise_for_status()
            if response.status_code == 200:
                return BeautifulSoup(response.content, 'html.parser')
        except requests.Timeout:
            # Handle timeout exception
            print(f"Request timed out! Retrying up to {url_retries - retry -1} more times.")
        except requests.ConnectionError:
            # Handle connection error
            print(f"Connection error occurred! Retrying up to {url_retries - retry -1} more times.")
        except requests.HTTPError as e:
            # Handle HTTP error
            print(f"HTTP error occurred: Retrying up to {url_retries - retry -1} more times.", e)
        except requests.TooManyRedirects:
            # Handle too many redirects error
            print(f"Too many redirects! Retrying up to {url_retries - retry -1} more times.")
        except requests.RequestException as e:
            # Handle other request exceptions
            print(f"An error occurred: Retrying up to {url_retries - retry -1} more times.", e)
    print(f"Max number of retries attempted({url_retries}).  Skipping.")
    return None

def save_to_csv(output_file, data):
    with open(output_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['URL', 'Content', 'Suggestions'])
        for row in data:
            writer.writerow(row)

def save_to_xlsx(output_file, data):
    df = pd.DataFrame(data)
    df.to_excel(output_file, index=False)

def scrape_intel_article_meta_data(soup):
    meta_data = {}
    # Extract topic
    meta_articleType_tag = soup.find('meta', {'name': 'format'})
    articleType = meta_articleType_tag.get('content', 'Not found') if meta_articleType_tag else "Not found"
    
    if articleType == 'articledetail':
        articleType = 'general'
    elif articleType == 'salesforce-article':
        articleType = 'reactive'
    else:
        articleType = ''
    meta_data['Article_Type'] = articleType

    # Extract meta Keywords
    meta_keywords_tag = soup.find('meta', {'name': 'keywords'})
    meta_data['Keywords'] = meta_keywords_tag.get('content', 'Not found') if meta_keywords_tag else "Not found"

    # Extract meta last modified date
    meta_lastModifiedDate_tag = soup.find('meta', {'name': 'lastModifieddate'})
    meta_data['lastModifiedDate'] = meta_lastModifiedDate_tag.get('content', 'Not found') if meta_lastModifiedDate_tag else "Not found"
    
    # Extract meta topic
    meta_topic_tag = soup.find('meta', {'name': 'topic'})
    meta_data['Article_Topic'] = meta_topic_tag.get('content', 'Not found') if meta_topic_tag else "Not found"

    return meta_data

def scrape_intel_reactive_article(soup):
    article_data = {}
    # Extract Article ID
    article_id_element = soup.find('span', {'class': 'article-id'})
    article_id = article_id_element.text.strip() if article_id_element else "Not found"
    split_string = article_id.split(': ', 1)
    article_data['Article_ID'] = split_string[1].strip() if len(split_string) > 1 else "Not found"

    # Extract Title
    title_element = soup.find('h1', {'class': 'h3'})
    article_data['Title'] = title_element.text.strip() if title_element else "Not found"

    # Extract Summary
    summary_element = soup.find('div', {'class': 'article-intro'})
    summary = summary_element.text.strip() if summary_element else "Not found"
    summary = re.search(r"^.*\n\s*(.*)", summary)
    article_data['Summary'] = summary.group(1) if summary else "Not found"

    # Extract Description
    description_element = soup.find('div', {'id': 'description'})
    description = description_element.text.strip() if description_element else "Not found"
    description = re.search(r"^.*\n\s*(.*)", description)
    article_data['Description'] = description.group(1) if description else "Not found"

    # Extract Resolution with HTML formatting
    resolution_element = soup.find('div', {'id': 'resolution'})
    article_data['Resolution'] = str(resolution_element) if resolution_element else "Not found"
    article_data['Resolution'] = md(article_data['Resolution'])
    
    # Extract Related Articles with HTML formatting
    related_articles_element = soup.find('div', {'class': 'relatedArticles'})
    article_data['Related_Articles'] = str(related_articles_element) if related_articles_element else "Not found"

    # Extract Products
    related_products_element = soup.find('div', {'class': 'blade-product-list-container'})
    if related_products_element:
        product_links = related_products_element.find_all('a', {'class': 'blade-product-list-item'})
        related_products = [link.text.strip() for link in product_links]
    else:
        related_products = "Not found"
    article_data['Products'] = related_products

    #article_data_str = f"Article ID: {article_data['Article_ID']}\n"
    #article_data_str += f"Title: {article_data['Title']}\n"
    #article_data_str += f"Summary: {article_data['Summary']}"
    #article_data_str += f"Description: {article_data['Description']}\n"
    #article_data_str += f"Resolution: {article_data_resolution_md}\n"
    #article_data_str += f"Related Articles: {article_data['Related_Articles']}\n"
    #article_data_str += f"Products{",".join(article_data['Products'])}"

    return article_data

def scrape_intel_general_article(soup):
    article_data = {}
    # Extract Article ID
    article_attributes_element = soup.find('div', {'class': 'article-attributes'})
    article_attributes = article_attributes_element.text.strip() if article_attributes_element else "Not found"
    article_attributes = re.search(r'ID\n\s*([0-9]*)\n', article_attributes)
    article_data['Article_ID'] = article_attributes.group(1) if article_attributes else 'Not found'

    # Extract Title
    title_element = soup.select_one('header > div > h1')
    article_data['Title'] = title_element.text.strip() if title_element else "Not found"

    # Extract Body with HTML formatting
    body_element = soup.find('article')
    article_data['Body'] = str(body_element) if body_element else "Not found"
    article_data['Body'] = md(article_data['Body'])

    # Extract Products
    related_products_element = soup.find('div', {'class': 'blade-product-list-container'})
    if related_products_element:
        product_links = related_products_element.find_all('a', {'class': 'blade-product-list-item'})
        related_products = [link.text.strip() for link in product_links]
    else:
        related_products = "Not found"
    article_data['Products'] = related_products

    return article_data

def suggestions_to_dict(url, article_type, suggestions):
    # Split the string into individual entries
    input_string = {'url':f"{url}",'type':f'{article_type}'}

    input_string = suggestions.split('\"\\n,\"')
    output_string = input_string

    return (output_string)
        
def main():
    os.system('clear')
    input_csv = 'Report.csv'
    proxy_setting = proxy_settings(True)

    with open('Intel Support KB Content Editor.md', 'r') as file:
        system_prompt = file.read()
    
    access_token, expiry_time = get_access_token(CLIENT_ID, CLIENT_SECRET, proxy_setting)
    urls = read_csv(input_csv)

    for url in urls:
        print(f"Processing URL: {url}")
        soup = fetch_page_content(url, proxy_setting, url_get_retries, url_get_timeout)
        if soup:
            # Extract meta information from the web page
            meta_data = scrape_intel_article_meta_data(soup)

            # If web article is reactive
            if meta_data['Article_Type'] == 'reactive':
                article_data = scrape_intel_reactive_article(soup)

            # If web article is general
            elif meta_data['Article_Type'] == 'general':
                article_data = scrape_intel_general_article(soup)
            
            article_data['url'] = url
            article_data_json = json.dumps(article_data)

        access_token, expiry_time = check_token_expiry(access_token, expiry_time, CLIENT_ID, CLIENT_SECRET)
        suggestions = invoke_model(access_token, system_prompt, article_data_json, proxy_setting)
        with open(f"./reviewed_articles/{article_data['Article_ID']}.md", "w") as file:
            file.write(suggestions)
        
        print(f"Review and suggestions saved to {article_data['Article_ID']}.md")
        time.sleep(5)

if __name__ == "__main__":
    main()

