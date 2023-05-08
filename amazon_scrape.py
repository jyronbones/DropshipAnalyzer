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


start_time = time.time()
domain_name = 'https://www.amazon.com/'
product_headers = ['product_title', 'product_price', 'regular_price', 'product_shipping',
                   'product_rating', 'amazon_prime', 'review_count', 'product_link',
                   'item_searched']
products_df = pd.DataFrame(columns=product_headers)
item = ''
product_df_list = []


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
    search_box = chrome_driver.find_element(By.CSS_SELECTOR, '[type="text"]')
    search_box.send_keys(item_to_search)
    chrome_driver.find_element(By.CSS_SELECTOR, '[type="submit"]').click()
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
    driver = page_products = ''
    temp_prod_df = pd.DataFrame(columns=product_headers)
    while True:
        try:
            proxy = random.choice(list(proxy_list.values()))
            #   load manufacturer page
            print(f'Proxy being used: {proxy}')
            driver = configure_driver(proxy)
            driver.get(domain_name)
            time.sleep(1)
            try:
                if 'Enter the characters you see below' in driver.find_element(By.TAG_NAME, 'h4').text:
                    print('Web Automation Detected')
                    driver.quit()
                else:
                    break
            except NoSuchElementException:
                print('Proxy successfully connected...')
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

            try:
                page_products = driver.find_elements(By.CSS_SELECTOR, '[data-component-type="s-search-result"]')
            except NoSuchElementException:
                print('NoSuchElementException: Could not locate products on page')

            for product in page_products:
                prod_results = []
                prod_title = prod_price = prod_price_dollar = prod_price_fraction = prod_shipping = supplier_rating = \
                    review_count = amazon_prime = product_link = regular_price = ''
                try:
                    prod_title = product.find_element(By.TAG_NAME, 'h2').text
                except NoSuchElementException:
                    print(f"NoSuchElementException: Product title")
                try:
                    prod_price_dollar = product.find_element(By.CLASS_NAME, 'a-price-whole').text
                except NoSuchElementException:
                    print(f"NoSuchElementException: No product price for: {prod_title}")
                try:
                    prod_price_fraction = driver.find_element(By.CLASS_NAME, 'a-price-fraction').text
                except NoSuchElementException:
                    print(f"NoSuchElementException: No product price for: {prod_title}")
                prod_price = f'{prod_price_dollar}.{prod_price_fraction}'
                prod_price = prod_price.replace(',', '')
                if prod_price == '0.0':
                    prod_price = '0'
                try:
                    regular_price = product.find_element(
                        By.CSS_SELECTOR, '[class="a-price a-text-price"]').find_element(
                        By.CLASS_NAME, 'a-offscreen').get_attribute('innerHTML')
                    regular_price = regular_price.replace(',', '')
                    regular_price = regular_price.replace('$', '')
                except NoSuchElementException:
                    print(f"NoSuchElementException: No regular price for: {prod_title}")
                # try:
                #     prod_shipping = product.find_element(By.CLASS_NAME, 'element-promotion-shipping-price__price').text
                #     if 'US' in prod_shipping:
                #         prod_shipping = prod_shipping.replace('+US$', '')
                #     else:
                #         prod_shipping = prod_shipping.replace('+', '')
                #         prod_shipping = prod_shipping.replace('$', '')
                # except NoSuchElementException:
                #     print(f"NoSuchElementException: No product shipping for: {prod_title}")
                # prod_shipping = prod_shipping.replace(',', '')
                # try:
                #     prod_min_qty = product.find_element(By.CLASS_NAME, 'element-offer-minorder-normal__value').text
                # except NoSuchElementException:
                #     print(f"NoSuchElementException: No product minimum quantity for: {prod_title}")
                try:
                    supplier_rating_html = product.find_element(
                        By.TAG_NAME, 'i').find_element(
                        By.CLASS_NAME, 'a-icon-alt').get_attribute('innerHTML')
                    p = '[\d]*[.][\d]+'
                    if re.search(p, supplier_rating_html) is not None:
                        for catch in re.finditer(p, supplier_rating_html):
                            supplier_rating = catch[0]
                except NoSuchElementException:
                    print(f"NoSuchElementException: No supplier_rating for: {prod_title}")
                    supplier_rating = '0'
                try:
                    prime_element = product.find_element(
                        By.CSS_SELECTOR, '[aria-label="Amazon Prime"]')
                    amazon_prime = 'YES'
                except NoSuchElementException:
                    amazon_prime = 'NO'
                try:
                    review_count = product.find_element(
                        By.CSS_SELECTOR, '[class="a-size-base s-underline-text"]').get_attribute('innerHTML')
                    review_count = review_count.replace(',', '')
                except NoSuchElementException:
                    print(f"NoSuchElementException: No review count for: {prod_title}")
                    review_count = '0'
                try:
                    product_link = product.find_element(
                        By.TAG_NAME, 'h2').find_element(By.TAG_NAME, 'a').get_attribute('href')
                except NoSuchElementException:
                    print(f"NoSuchElementException: No common review for: {prod_title}")
                prod_results.extend([prod_title, prod_price, regular_price, prod_shipping, supplier_rating,
                                     amazon_prime, review_count, product_link, search_item])
                temp_prod_df.loc[len(temp_prod_df)] = prod_results
            break
            next_page = driver.find_element(
                By.CSS_SELECTOR, '[class="s-pagination-item s-pagination-next s-pagination-button s-pagination-separator"]')
            next_page.click()
        except NoSuchElementException:
            print(f'End of pages for {search_item}')
            break

    driver.quit()

    temp_prod_df['date'] = date.today()
    return temp_prod_df


# with ThreadPoolExecutor(max_workers=3) as ex:
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
    shutil.move('products.csv', r'data\amazon\products.csv')
    end_time = time.time()
    scraped_time = (end_time - start_time) / 60 / 60
    print(f'Total scrape time = {scraped_time:.2f} hours')
    products_df = products_df.drop_duplicates(keep='first')
    products_df['product_price'] = products_df['product_price'].fillna(0)
    products_df['product_price'] = products_df['product_price'].astype('float')
    # products_df['regular_price'] = products_df['regular_price'].fillna(0)
    # products_df['regular_price'] = products_df['regular_price'].astype('float')
    products_df['review_count'] = products_df['review_count'].fillna(0)
    products_df['review_count'] = products_df['review_count'].astype('int')
    products_df['product_rating'] = products_df['product_rating'].fillna(0)
    products_df['product_rating'] = products_df['product_rating'].astype('float')
    products_df = products_df.fillna('NA')
    return products_df