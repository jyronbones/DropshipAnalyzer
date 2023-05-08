import glob
import pandas as pd
import pyodbc as pyodbc


# def all_results():
#     r_set = my_conn.execute('SELECT * FROM amazon_db.dbo.temp_table')
#     return r_set


def df_to_temp_amazon_table():
    print('Connecting to SQL Server...')
    cnxn = pyodbc.connect(
        'Driver=ODBC Driver 17 for SQL Server;'
        'Server=LocalHost;'
        'Database=dropship_db;'
        'Trusted_connection=yes;'
    )
    cursor = cnxn.cursor()

    print('Creating df from csv files....')
    all_files = glob.glob(
        r"C:\Users\byron\OneDrive\Desktop\Programs\Python\dropship_analytics\amazon_gui\data\amazon\*.csv")
    df = pd.concat((pd.read_csv(f) for f in all_files))
    df = df.drop_duplicates(keep='first')
    df['product_price'] = df['product_price'].fillna(0)
    df['product_price'] = df['product_price'].astype('float')
    df['regular_price'] = df['regular_price'].fillna(0)
    df['regular_price'] = df['regular_price'].astype('float')
    df['review_count'] = df['review_count'].fillna(0)
    df['review_count'] = df['review_count'].astype('int')
    df['product_rating'] = df['product_rating'].fillna(0)
    df['product_rating'] = df['product_rating'].astype('float')
    df['product_shipping'] = df['product_shipping'].fillna(0)
    df['product_shipping'] = df['product_shipping'].astype('float')
    df = df.fillna('NA')

    print('Creating db temp_amazon_table...')
    cursor.execute('''
            CREATE TABLE dbo.temp_amazon_table (
                title varchar (3000),
                price float,
                regular_price float,
                shipping_cost float,
                product_rating float,
                amazon_prime varchar (10),
                review_count int,
                product_link varchar (500),
                item_searched varchar (255),
                date date
                )
                   ''')

    cnxn.commit()

    print('exporting data from df to db temp_amazon_table...')
    sql_temp_attr_stmt = "INSERT INTO dbo.temp_amazon_table values (?,?,?,?,?,?,?,?,?,?)"
    cursor.executemany(sql_temp_attr_stmt, df.values.tolist())

    cnxn.commit()
    cursor.close()
    return df


def df_to_temp_baba_table():
    print('Connecting to SQL Server...')
    cnxn = pyodbc.connect(
        'Driver=ODBC Driver 17 for SQL Server;'
        'Server=LocalHost;'
        'Database=dropship_db;'
        'Trusted_connection=yes;'
    )
    cursor = cnxn.cursor()

    print('Creating df from csv files....')
    all_files = glob.glob(
        r"C:\Users\byron\OneDrive\Desktop\Programs\Python\dropship_analytics\amazon_gui\data\alibaba\*.csv")
    df = pd.concat((pd.read_csv(f) for f in all_files))
    df = df.drop_duplicates(keep='first')
    df['product_price'] = df['product_price'].fillna(0)
    df['product_price'] = df['product_price'].astype('float')
    df['approx_cdn_price'] = df['approx_cdn_price'].fillna(0)
    df['approx_cdn_price'] = df['approx_cdn_price'].astype('float')
    df['review_count'] = df['review_count'].fillna(0)
    df['review_count'] = df['review_count'].astype('int')
    df['product_rating'] = df['product_rating'].fillna(0)
    df['product_rating'] = df['product_rating'].astype('float')
    df['product_shipping'] = df['product_shipping'].fillna(0)
    df['product_shipping'] = df['product_shipping'].astype('float')
    df = df.fillna('NA')

    print('Creating db temp_baba_table...')
    cursor.execute('''
            CREATE TABLE dbo.temp_baba_table (
                title varchar (3000),
                price float,
                price_range varchar (255),
                approx_cdn_price float,
                shipping_cost float,
                min_qty varchar (255),
                supplier_rating float,
                supplier_verified varchar (10),
                review_count int,
                common_review varchar (255),
                product_link varchar (500),
                item_searched varchar (255),
                date date
                )
                   ''')

    cnxn.commit()

    print('exporting data from df to db temp_baba_table...')
    sql_temp_attr_stmt = "INSERT INTO dbo.temp_baba_table values (?,?,?,?,?,?,?,?,?,?,?,?,?)"
    cursor.executemany(sql_temp_attr_stmt, df.values.tolist())

    cnxn.commit()
    cursor.close()
    return df


def delete_tables():
    print('Connecting to SQL Server...')
    cnxn = pyodbc.connect(
        'Driver=ODBC Driver 17 for SQL Server;'
        'Server=LocalHost;'
        'Database=dropship_db;'
        'Trusted_connection=yes;'
    )
    cursor = cnxn.cursor()

    cursor.execute("DROP TABLE dbo.temp_amazon_table")
    cursor.execute("DROP TABLE dbo.temp_baba_table")
    cnxn.commit()
    cursor.close()
    return None


def temp_to_main():
    print('Connecting to SQL Server...')
    cnxn = pyodbc.connect(
        'Driver=ODBC Driver 17 for SQL Server;'
        'Server=LocalHost;'
        'Database=dropship_db;'
        'Trusted_connection=yes;'
    )
    cursor = cnxn.cursor()

    cursor.execute("INSERT INTO dropship_db.dbo.amazon_products(title, price, regular_price, shipping_cost, "
                   "product_rating, amazon_prime, review_count, product_link, item_searched, date) "
                   "SELECT tt.title, tt.price, tt.regular_price, tt.shipping_cost, tt.product_rating, "
                   "tt.amazon_prime, tt.review_count, tt.product_link, tt.item_searched, tt.date "
                   "FROM dropship_db.dbo.temp_amazon_table as tt "
                   "WHERE NOT EXISTS (SELECT title, price, regular_price, shipping_cost, product_rating, "
                   "amazon_prime, review_count, product_link, item_searched "
                   "FROM dropship_db.dbo.amazon_products "
                   "WHERE title = tt.title AND price = tt.price "
                   "AND regular_price = tt.regular_price "
                   "AND shipping_cost = tt.shipping_cost "
                   "AND product_rating = tt.product_rating "
                   "AND amazon_prime = tt.amazon_prime "
                   "AND review_count = tt.review_count "
                   "AND product_link = tt.product_link "
                   "AND item_searched = tt.item_searched)")

    cursor.execute("INSERT INTO dropship_db.dbo.alibaba_products(title, price, price_range, approx_cdn_price, "
                   "shipping_cost, min_qty, supplier_rating, supplier_verified, review_count, common_review, "
                   "product_link, item_searched, date) "
                   "SELECT tt.title, tt.price, tt.price_range, tt.approx_cdn_price, "
                   "tt.shipping_cost, tt.min_qty, tt.supplier_rating, tt.supplier_verified, tt.review_count, "
                   "tt.common_review, tt.product_link, tt.item_searched, tt.date "
                   "FROM dropship_db.dbo.temp_baba_table as tt WHERE NOT EXISTS (SELECT title, price, price_range, "
                   "approx_cdn_price, shipping_cost, min_qty, supplier_rating, supplier_verified, review_count, "
                   "common_review, product_link, item_searched "
                   "FROM dropship_db.dbo.alibaba_products "
                   "WHERE title = tt.title "
                   "AND price = tt.price "
                   "AND price_range = tt.price_range "
                   "AND approx_cdn_price = tt.approx_cdn_price "
                   "AND shipping_cost = tt.shipping_cost "
                   "AND min_qty = tt.min_qty "
                   "AND supplier_rating = tt.supplier_rating "
                   "AND review_count = tt.review_count "
                   "AND common_review = tt.common_review "
                   "AND product_link = tt.product_link "
                   "AND item_searched = tt.item_searched)")
    cnxn.commit()
    cursor.close()
    return None


# df_to_temp_baba_table()
# df_to_temp_amazon_table()
# all_results()
