import hashlib
import json
import os
import time
import xml.etree.ElementTree as ET
from datetime import date, datetime
from typing import Any, Dict

import pandas as pd
import psycopg2
import requests
import telegram_send
from google.oauth2 import service_account
from googleapiclient import discovery
from sqlalchemy import create_engine


class Read_data():
    def _init_(self):
        # to store and renew all data
        self.entry = {}

    def read_data(self):
        """
        Reads data from the Google Sheet with id = spreadsheet_id.
        Reads the current rate of dolllar.
        Takes the service account credentials from the "credentials.json" file.
        Saves data to dictionary "values".
        Returns that values.
        """
        try:
            scopes = ["https://www.googleapis.com/auth/drive",
                      "https://www.googleapis.com/auth/drive.file",
                      "https://www.googleapis.com/auth/spreadsheets"]
            secret_file = os.path.join(os.getcwd(), 'credentials.json')

            spreadsheet_id = '1GGymB67F6TNUaHNDnHv4hLynmpgL9bcYCA1TJTT38WE'
            # range_name = 'Sheet1!A1:F2'

            credentials = service_account.\
                Credentials.from_service_account_file(secret_file,
                                                      scopes=scopes)
            service = discovery.build('sheets', 'v4', credentials=credentials)

            values = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range='A1:D60',
                majorDimension='COLUMNS').execute()

            # print(values)
            return values

        except OSError as e:
            print(e)

        return

    def convert_data_to_dict(self) -> dict:
        """
        Converts lists to tuples.
        Converts strings to ints.
        Makes proper dict for later usage.
        """
        data = self.read_data()
        data = data['values']
        self.entry = {
            "№": tuple(map(int, data[0][1:])),
            "заказ №": tuple(map(int, data[1][1:])),
            "стоимость,$": tuple(map(int, data[2][1:])),
            "срок поставки": tuple(data[3][1:]),
            "стоимость в рублях": ()
        }
        # print(self.entry)
        return self.entry

    def check_dollar_price(self):
        data_dollar = {}
        request = requests.get('https://www.cbr.ru/scripts/XML_daily.asp')
        root = ET.fromstring(request.content)
        for child in root.iter('Valute'):
            if child.attrib == {'ID': 'R01235'}:
                for item in child:
                    data_dollar[item.tag] = item.text

        dollar_price = data_dollar['Value']
        print(dollar_price)
        return dollar_price

    def convert_to_date_format(self) -> tuple:
        """
        Converts dates from str format to datetime.date format.
        Returns tuple of formetted data.
        """
        unconverted_dates = self.convert_data_to_dict()["срок поставки"]
        converted_dates = ()
        for i in unconverted_dates:
            i = i.replace(".", "/")
            i = datetime.strptime(i, '%d/%m/%Y').date()
            converted_dates += (i,)
        self.entry["срок поставки"] = converted_dates
        # print(converted_dates)
        return converted_dates

    def usd_to_rub(self) -> tuple:
        """
        Gets the current dollar price.
        Counts the price in rubles, holds it in the tuple.
        Returns that tuple.
        """
        results = self.convert_data_to_dict()["стоимость,$"]
        rub_price_tuple = ()
        dollar_price = float(self.check_dollar_price().replace(",", "."))
        for i in results:
            i = i * dollar_price
            rub_price_tuple += (i,)
        self.entry["стоимость в рублях"] = rub_price_tuple
        return rub_price_tuple

    def pandas_df(self) -> None:
        """
        Shows the data conviniently in Pandas dataframe format
        """
        self.read_data()
        self.convert_data_to_dict()
        self.check_dollar_price()
        self.convert_to_date_format()
        self.usd_to_rub()
        data = self.entry
        df = pd.DataFrame(data)
        print(df)
        return df


m = Read_data()
m.pandas_df()


class Postgre_DB(Read_data):
    def connect_to_db(self) -> None:
        """
        Connects, creates table with name "data".
        Writes down the data in DB, print the data.
        """

        conn_string = 'postgresql://myprojectuser:password@localhost/myproject'
        db = create_engine(conn_string)
        conn = db.connect()

        df = self.pandas_df()
        df.to_sql('data', con=conn, if_exists='replace',
                  index=True)
        conn = psycopg2.connect(conn_string)
        conn.autocommit = True
        cursor = conn.cursor()

        # show the data from DB
        sql1 = '''select * from data;'''
        cursor.execute(sql1)
        for i in cursor.fetchall():
            print(i)

        conn.commit()
        conn.close()
        pass


p = Postgre_DB()
p.connect_to_db()


class Telegram_notifications(Read_data):
    """
    Check if the delivery period has passed
    If passed the notification to telegram bot
    https://telegram.me/job_task_bot is sended
    """
    def check_dates(self):
        i = 0
        dates = self.convert_to_date_format()
        for day in dates:
            i += 1
            if date.today() > day:
                telegram_send.send(
                    messages=[
                        f"Time for delivery of order number:{i} has passed"])


t = Telegram_notifications()
t.check_dates()


class Check_data_online(Postgre_DB, Telegram_notifications):
    """
    Gets the data from sheet.
    Stores it in a var then get a hash of that var.
    In 10 seconds retrieve data again, and compare
    current hash to the previous one.
    If hashes are identical: do not change data in storage.
    Else: change it to the latest version.
    """
    def make_hash(self, dictionary: Dict[str, Any]):
        """MD5 hash of a dictionary."""
        dhash = hashlib.md5()
        encoded = json.dumps(dictionary, sort_keys=True).encode()
        dhash.update(encoded)
        return dhash.hexdigest()

    def compare_hashes(self) -> bool:
        """
        Makes a hash of a get responce from sheet
        Waits 3 sec
        Gets another responce, make hash
        Compares two hashes
        If hashes are identical: returns 0.
        Else: returns 1.
        In 3 sec repeats.
        """
        while True:
            try:
                # perform the get request and store it in a var
                first_response = self.read_data()
                # create a hash
                first_hash = self.make_hash(first_response)
                # wait for 3 seconds
                time.sleep(3)

                # perform the get request
                second_response = self.read_data()

                # create a new hash
                second_hash = self.make_hash(second_response)

                # check if new hash is same as the previous hash
                if first_hash == second_hash:
                    pass

                # if something changed in the hashes
                else:
                    # change data
                    self.connect_to_db()
                    pass

            # To handle exceptions
            except Exception as e:
                print("error", e)


h = Check_data_online()
h.compare_hashes()
