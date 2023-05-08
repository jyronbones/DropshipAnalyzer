import shutil
from datetime import date
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from seleniumwire import webdriver
import pandas as pd
import time
import re
import random
from concurrent.futures import ThreadPoolExecutor

from urllib3.exceptions import MaxRetryError

start_time = time.time()
domain_name = 'https://www.alibaba.com/'
product_headers = ['product_title', 'product_price', 'price_range', 'approx_cdn_price', 'product_shipping',
                   'product_min_qty', 'product_rating', 'supplier_verified', 'review_count', 'common_review',
                   'product_link', 'item_searched']
products_df = pd.DataFrame(columns=product_headers)
item = ''
product_df_list = []


def get_products_list():
    products_file = 'products_list.txt'
    with open(products_file) as file:
        lines = file.readlines()
        lines = [line.rstrip() for line in lines]
    return lines


# returns a random proxy from proxy.txt
def read_proxies(filename):
    scheme = 'https://'
    proxies = {}
    with open(filename) as file:
        for line in file:
            pr = line.strip()
            m = re.search(r'(.*):(.*):(.*):(.*)', pr)
            proxies[scheme + m.group(1)] = scheme + m.group(3) + ':' + m.group(4) + '@' + m.group(1) + ':' + m.group(2)
    return proxies


#   configures Chrome driver options
def configure_driver(proxy):
    print('Configuring driver...')
    options = webdriver.ChromeOptions()
    options.headless = True
    options.add_argument('start-maximized')
    options.add_argument("window-size=1900,1080")
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        "AppleWebKit/537.36 (KHTML, like Gecko)"
        "Chrome/87.0.4280.141 Safari/537.36"
    )
    p_options = {
        'proxy': {
            'https': proxy,
        }
    }
    c_driver = webdriver.Chrome(options=options,
                                seleniumwire_options=p_options,
                                executable_path='chromedriver.exe')
    return c_driver


def search_product(chrome_driver, item_to_search):
    search_box = chrome_driver.find_element(By.XPATH,
                                            '//*[@id="J_SC_header"]/header/div[2]/div[3]/div/div[2]/form/div[2]/input')
    search_box.send_keys(item_to_search)
    time.sleep(1)
    chrome_driver.find_element(By.XPATH, '//*[@id="J_SC_header"]/header/div[2]/div[3]/div/div[2]/form/input[5]').click()
    print(f"Searching item: {item_to_search}...")
    return item_to_search


# scrolls to bottom of page
def scroll_to_end(chrome_driver):
    page = ''
    scroll_pause_time = 0.5

    last_height = chrome_driver.execute_script("return document.body.scrollHeight")  # get scroll height
    height_flag = 0
    while True:
        if height_flag == 0:
            page = chrome_driver.find_element(By.CSS_SELECTOR, 'body')
            height_flag = 1
        for i in range(0, 20):
            page.send_keys(Keys.PAGE_DOWN)
            time.sleep(scroll_pause_time)  # Wait to load page

        # Calculate new scroll height and compare with last scroll height
        new_height = chrome_driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            return None
        last_height = new_height


proxy_list = read_proxies("proxies.txt")


def item_scrape(item):
    driver = ''
    temp_prod_df = pd.DataFrame(columns=product_headers)
    while True:
        try:
            proxy = random.choice(list(proxy_list.values()))
            #   load manufacturer page
            print(f'Proxy being used: {proxy}')
            driver = configure_driver(proxy)
            driver.get(domain_name)
            time.sleep(1)
            break
        except Exception:
            print('Proxy unsuccessfully connected...')
            driver.quit()

    try:
        cookie_button = driver.find_element(By.XPATH, '//*[@id="GDPR-cookies-notice"]/div[2]/div/div[2]/div[1]')
        cookie_button.click()
    except NoSuchElementException:
        print("Accept Cookies prompt not present")

    search_item = search_product(driver, item)
    while True:
        try:
            scroll_to_end(driver)
            current_url = driver.current_url

            try:
                cookie_button = driver.find_element(By.XPATH, '//*[@id="GDPR-cookies-notice"]/div[2]/div/div[2]/div[1]')
                cookie_button.click()
            except NoSuchElementException:
                print("Accept Cookies prompt not present")

            while True:
                try:
                    search_contents = driver.find_element(By.CLASS_NAME, 'app-organic-search__content')
                    break
                except NoSuchElementException:
                    driver.quit()
                    driver.get(current_url)

            page_products = search_contents.find_elements(By.CSS_SELECTOR, '[data-traffic-product="true"]')
            for product in page_products:
                price_flag = False
                title_flag = False
                prod_results = []
                prod_title = prod_price = approx_cdn_price = prod_min_qty = prod_shipping = supplier_rating = review_count = \
                    common_review = verified_supplier = product_link = price_range = ''
                try:
                    prod_title = product.find_element(By.CLASS_NAME, 'elements-title-normal__content.large').text
                except NoSuchElementException:
                    print(f"NoSuchElementException: Product title1")
                    title_flag = True
                if title_flag:
                    try:
                        prod_title = product.find_element(By.CLASS_NAME, 'elements-title-normal__outter').text
                    except NoSuchElementException:
                        print(f"NoSuchElementException: Product title2")
                try:
                    prod_price = product.find_element(By.CLASS_NAME, 'elements-offer-price-normal__promotion').text
                    if 'US' in prod_price:
                        prod_price = prod_price.replace('US', '')
                        prod_price = prod_price.replace('$', '')
                        if '-' in prod_price:
                            price_range = prod_price
                            prod_prices = prod_price.split('-')
                            prod_price = prod_prices[0]
                    else:
                        prod_price = product.find_element(By.CLASS_NAME, 'elements-offer-price-normal__promotion').text
                        prod_price = prod_price.replace('$', '')
                        if '-' in prod_price:
                            price_range = prod_price
                            prod_prices = prod_price.split('-')
                            prod_price = prod_prices[0]
                except NoSuchElementException:
                    price_flag = True
                    print(f"NoSuchElementException: No product price for: {prod_title}")
                if price_flag:
                    try:
                        if 'US' in prod_price:
                            price_range = prod_price.replace('US', '')
                            prod_prices = price_range.split('-')
                            prod_price = prod_prices[0]
                        else:
                            price_range = product.find_element(By.CLASS_NAME, 'elements-offer-price-normal__price').text
                            price_range = price_range.replace('$', '')
                            prod_prices = price_range.split('-')
                            prod_price = prod_prices[0]
                    except NoSuchElementException:
                        print(f"NoSuchElementException: No product price for: {prod_title}")
                prod_price = prod_price.replace(',', '')
                try:
                    prod_shipping = product.find_element(By.CLASS_NAME, 'element-promotion-shipping-price__price').text
                    if 'US' in prod_shipping:
                        prod_shipping = prod_shipping.replace('+US$', '')
                    else:
                        prod_shipping = prod_shipping.replace('+', '')
                        prod_shipping = prod_shipping.replace('$', '')
                except NoSuchElementException:
                    print(f"NoSuchElementException: No product shipping for: {prod_title}")
                    prod_shipping = '0'
                prod_shipping = prod_shipping.replace(',', '')
                try:
                    prod_min_qty = product.find_element(By.CLASS_NAME, 'element-offer-minorder-normal__value').text
                except NoSuchElementException:
                    print(f"NoSuchElementException: No product minimum quantity for: {prod_title}")
                try:
                    supplier_rating = product.find_element(By.CLASS_NAME,
                                                           'seb-supplier-review-gallery-test__score').text
                except NoSuchElementException:
                    print(f"NoSuchElementException: No supplier_rating for: {prod_title}")
                    supplier_rating = '0'
                try:
                    verified_element = product.find_element(
                        By.CLASS_NAME, 'supplier-tag-popup_base')
                    verified_supplier = 'YES'
                except NoSuchElementException:
                    verified_supplier = 'NO'
                try:
                    review_count = product.find_element(By.CLASS_NAME, 'seb-supplier-review__review-count').text
                    review_count = review_count.replace('(', '')
                    review_count = review_count.replace(')', '')
                except NoSuchElementException:
                    print(f"NoSuchElementException: No review count for: {prod_title}")
                    review_count = '0'
                try:
                    common_review = product.find_element(
                        By.CSS_SELECTOR, '[class="seb-supplier-review__reviews has-score"]').text
                    common_review = common_review.replace('"', "")
                except NoSuchElementException:
                    print(f"NoSuchElementException: No common review for: {prod_title}")
                try:
                    product_link = product.find_element(
                        By.CSS_SELECTOR, '[class="elements-title-normal__outter"]').find_element(By.TAG_NAME,
                                                                                                 'a').get_attribute(
                        'href')
                except NoSuchElementException:
                    print(f"NoSuchElementException: No common review for: {prod_title}")
                prod_price = prod_price.replace('US', '')
                approx_cdn_price = float(prod_price) * 1.31
                approx_cdn_price = '{0:.2f}'.format(approx_cdn_price)
                approx_cdn_price = str(approx_cdn_price)
                prod_results.extend([prod_title, prod_price, price_range, approx_cdn_price, prod_shipping, prod_min_qty,
                                     supplier_rating, verified_supplier, review_count, common_review, product_link,
                                     search_item])
                temp_prod_df.loc[len(temp_prod_df)] = prod_results
            break
            next_page = driver.find_element(By.CSS_SELECTOR, '[class="seb-pagination__pages-link pages-next"]')
            next_page.click()
        except NoSuchElementException:
            print(f'End of pages for {search_item}')
            break

    driver.quit()

    temp_prod_df['date'] = date.today()
    return temp_prod_df


# with ThreadPoolExecutor(max_workers=1) as ex:
#     results = ex.map(item_scrape, products_list)
#
#     for df in results:
#         product_df_list.append(df)

def scrape(product_list):
    start_time = time.time()
    for item in product_list:
        df = item_scrape(item)
        product_df_list.append(df)

    products_df = pd.concat(product_df_list)
    products_df.to_csv(f'products.csv', index=False)
    shutil.move('products.csv', r'data\alibaba\products.csv')
    end_time = time.time()
    scraped_time = (end_time - start_time) / 60 / 60
    print(f'Total scrape time = {scraped_time:.2f} hours')
    products_df = products_df.drop_duplicates(keep='first')
    products_df['product_price'] = products_df['product_price'].fillna(0)
    products_df['product_price'] = products_df['product_price'].astype('float')
    products_df['approx_cdn_price'] = products_df['approx_cdn_price'].fillna(0)
    products_df['approx_cdn_price'] = products_df['approx_cdn_price'].astype('float')
    products_df['review_count'] = products_df['review_count'].astype('int')
    products_df['product_rating'] = products_df['product_rating'].fillna(0)
    products_df['product_rating'] = products_df['product_rating'].astype('float')
    products_df['product_shipping'] = products_df['product_shipping'].fillna(0)
    products_df['product_shipping'] = products_df['product_shipping'].astype('float')
    products_df = products_df.fillna('NA')
    return products_df

