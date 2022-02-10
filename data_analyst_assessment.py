import os
import logging
import mysql.connector #mysql connector
import psycopg2 #postgresql connector
import pandas as pd
from sqlalchemy import create_engine


# Setting chunk size
CHUNK_SIZE = 100

# For security, username and password are stored in environment variable
user_name = os.environ.get('batest_db_user')
password = os.environ.get('batest_db_password')

# MYSQL Connector
mysql_connection = mysql.connector.connect(
        host='localhost',
        db='batest',
        user=user_name,
        password=password
    )
print('MySQL connected successfully',mysql_connection)


postgres_engine = create_engine(f'postgresql+psycopg2://{user_name}:{password}@localhost/batest_postgres')
print('Postgres connected successfully',postgres_engine)


# Get a list of all table in database
batest_tables = pd.read_sql('SHOW TABLES FROM batest', mysql_connection)
batest_tables

# Converts snake_case to camelCase
def toCamelCase(col):
        # saving first and rest using split()
        first, *rest = col.split('_')

        # make first word lower and the rest titlecase
        return ''.join([first.lower(), *map(str.title, rest)])

# 1. Read data from an MYSQL database in **chunks**
# 2. Convert all the column names into camel case
# 3. Load the data into the PostgreSQL database in **chunks**
# 4. Read the data from PostgreSQL and write it into an Excel File.
with pd.ExcelWriter("solomon_data_analyst_assessment.xlsx") as writer:
    for table in batest_tables['Tables_in_batest']:
        print(table)
        # Read data from an MYSQL database in **chunks**
        table_gen = pd.read_sql(f'SELECT * FROM {table}', mysql_connection, chunksize=CHUNK_SIZE)
        print('Chunk data collected in table generator successfully')

        table_arr = []

        for chuck in table_gen:
            # Convert all the column names into camel case
            chuck.columns = chuck.columns.map(lambda x: toCamelCase(x))
            table_arr.append(chuck)
        print('Columns converted to camel case')


        table_large = pd.concat(table_arr)
        print('Chunk data combined successfully')

        # Load the data into the PostgreSQL database in **chunks**
        table_large.to_sql(
            table,
            postgres_engine,
            index=False,
            if_exists='replace',
            chunksize=CHUNK_SIZE
        )
        print('Load data in chunk succeefully to postgres')

        df_postgres = pd.read_sql(f'SELECT * FROM batest_postgres.public."{table}"', postgres_engine)
        print('Data read from postgres successfully')
        
         
        df_postgres.to_excel(writer, sheet_name=table, index=False)
        print(f'{table} written into excel\n')

