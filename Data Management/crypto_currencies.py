from datetime import datetime
from datetime import timedelta
from itertools import zip_longest
import json
import time as t
import os
import pickle
import happybase
import numpy as np
import pandas as pd
import utility
import struct

class CryptoHandler(object):
    """Class to handle cryprocurrency download and storage"""

    def __init__(self, download_api, data_struct):
        """Factory method"""

        self.api = download_api
        self.data_struct = data_struct

    def get_crypto_data(self, poloniex_pair, start_ts, end_ts, period):
        """Retrieve cryptocurrency data from Poloniex"""

        json_url = self.api.format(poloniex_pair, start_ts, end_ts, period)
        data_df = self.get_json_data(json_url)
        return data_df

    def get_json_data(self, json_url):
        """Download JSON data, return as a dataframe."""

        df = pd.read_json(json_url)
        return df

    def insert_row(self, batch, row):
        """Insert a row into HBase.
        Write the row to the batch. When the batch size is reached, rows will
        be sent to the database."""

        keyrow = self.prepare_key(row)
        data = self.prepare_data(row)
        batch.put(keyrow, data)

    def build_altcoin(self, btc_datum, crypto_datum):
        """Add altcoin/usd exchange data"""
        
        crypto_datum_insert = crypto_datum
        try:
            crypto_datum_insert["high_usd"] = float(crypto_datum["high"] * btc_datum["high"])
            crypto_datum_insert["low_usd"] = float(crypto_datum["low"] * btc_datum["low"])
            crypto_datum_insert["open_usd"] = float(crypto_datum["open"] * btc_datum["open"])
            crypto_datum_insert["close_usd"] = float(crypto_datum["close"] * btc_datum["close"])
            crypto_datum_insert["volume_usd"] = float(crypto_datum["volume"] * btc_datum["volume"])
            crypto_datum_insert["quote_volume_usd"] = float(crypto_datum["quoteVolume"] * btc_datum["quoteVolume"])
            crypto_datum_insert["weighted_average_usd"] = float(crypto_datum["weightedAverage"] * btc_datum["weightedAverage"])
        except Exception as e:
            crypto_datum_insert["high_usd"] = float(0)
            crypto_datum_insert["low_usd"] = float(0)
            crypto_datum_insert["open_usd"] = float(0)
            crypto_datum_insert["close_usd"] = float(0)
            crypto_datum_insert["volume_usd"] = float(0)
            crypto_datum_insert["quote_volume_usd"] = float(0)
            crypto_datum_insert["weighted_average_usd"] = float(0)        
        return crypto_datum_insert

    def prepare_key(self, row):
        """Prepare key data"""

        coin = str(row[8])
        timestamp = int(row[1].timestamp())
        keyrow = coin + str(timestamp)
        return keyrow

    def prepare_data(self, row):
        """Prepare data for bitcoin and altcoin"""

        insert_struct = self.data_struct[0].get("default")
        coin = str(row[8])
        timestamp = int(row[1].timestamp())
        date_object = row[1]
        read_at = date_object.strftime("%Y-%m-%d %H:%M:%S")
        date = date_object.date().strftime("%Y-%m-%d")
        time = date_object.time().strftime("%H:%M:%S")
        keyrow = coin + str(row[1].timestamp())
        base_values = [coin, struct.pack("L", timestamp), date, time,
                         read_at, struct.pack("f", row[2]),
                         struct.pack("f", row[3]), struct.pack("f", row[4]),
                         struct.pack("f", row[0]), struct.pack("f", row[6]),
                         struct.pack("f", row[5]), struct.pack("f", row[7])]

        values = base_values

        try:
            high_usd = row[9]
            low_usd = row[10]
            open_usd = row[11]
            close_usd = row[12]
            volume_usd = row[13]
            quote_volume_usd = row[14]
            weighted_average_usd = row[15]

            usd_values = [struct.pack("f", high_usd), struct.pack("f", low_usd),
                          struct.pack("f", open_usd), struct.pack("f", close_usd),
                          struct.pack("f", volume_usd), struct.pack("f", quote_volume_usd),
                          struct.pack("f", weighted_average_usd)]

            insert_struct = insert_struct + self.data_struct[1].get("added")
            values = values + usd_values

        except IndexError as e:
            pass
        # Unisco la struttura con i suoi valori
        data = dict(zip_longest(insert_struct, values))
        # Cancello eventuali valori spaiati
        try:
            del data[None]
        except:
            pass
        return data


def main():

    # Carico la configurazione
    CONFIG_FILE_PATH = "config.yaml"
    print("\nGetting {} as configuration file\n".format(CONFIG_FILE_PATH))
    config_helper = utility.ConfigHelper(CONFIG_FILE_PATH)
    config = config_helper.get_configuration()
    # Carico le sezioni necessarie
    default_section = config.get("default")
    crypto_section = config.get("crypto_currencies")
    twitter_section = config.get("twitter")
    # Definisco le costanti
    HOST = default_section.get("host")
    TABLE = default_section.get("hbasedb")
    BATCH_SIZE = default_section.get("hbasebatch")
    PERIOD = crypto_section.get("period")
    POLO_URL = crypto_section.get("polo_url")
    COMMAND = crypto_section.get("command")
    PARAMETERS = crypto_section.get("parameters")
    ALTCOINS = crypto_section.get("altcoins")
    QUOT_STRUCT = crypto_section.get("data_struct")
    start_date = default_section.get("start_date")
    start_date = datetime.combine(start_date, datetime.min.time())
    end_date = default_section.get("end_date")
    end_date = datetime.combine(end_date, datetime.min.time())

    BASE_POLO_URL = POLO_URL + COMMAND + PARAMETERS
    # Faccio partire il server Thrift
    print("Starting Thrift Server")
    os.system("nohup hbase thrift start -threadpool &")
    try:
        # Connetto a HBase
        print("Connecting to " + HOST)
        connection = happybase.Connection(HOST)
        print("Opening Connection")
        connection.open()
        # Recupero la tabella
        print("Getting Table " + TABLE)
        dbTable = connection.table(TABLE)
        # Imposto la dimensione del batch
        print("Set Batch Size to : %d" %  BATCH_SIZE)
        batch = dbTable.batch(batch_size=BATCH_SIZE)

        CryptoManager = CryptoHandler(BASE_POLO_URL, QUOT_STRUCT)

        # while True:
            # temp_date = datetime.now()
            # if ((temp_date - start_date).total_seconds() >= PERIOD):
                # end_date = temp_date

        crypto_data = None
        altcoin_data = None
        download_time = t.monotonic()
        print("Getting BTC data...")
        coinpair = "USDT_BTC"
        crypto_data = CryptoManager.get_crypto_data(coinpair,
                                        start_date.timestamp(),
                                        end_date.timestamp(), PERIOD)
        # Assegno la colonna valuta
        crypto_data["coin"] = "BTC"
        for altcoin in ALTCOINS:
            print("Getting {} data...".format(altcoin))
            coinpair = "BTC_{}".format(altcoin)
            altcoin_data = CryptoManager.get_crypto_data(coinpair,
                                        start_date.timestamp(),
                                        end_date.timestamp(), PERIOD)

            # Assegno la colonna valuta
            altcoin_data["coin"] = altcoin
            # aggiungo il df creato
            print("Merging data...")
            crypto_data = pd.concat([crypto_data, altcoin_data])
            
            elapsed_time = t.monotonic() - download_time
            record_no = len(crypto_data.index)
            print("{} quotations downloaded in {} s\n".format(record_no,
                                                              elapsed_time))
        # Leggo il dato di riferimento "BTC"
        for index, crypto_datum in crypto_data.iterrows():
            if crypto_datum["coin"] == "BTC":
               crypto_datum_insert = crypto_datum
            else:
                btc_datum = crypto_data.loc[(crypto_data["coin"] == "BTC") & (crypto_data["date"] == crypto_datum["date"])]
                crypto_datum_insert = CryptoManager.build_altcoin(btc_datum, crypto_datum)
            # Inserisci su HBase
            print("Adding records on batch...")
            try:
                CryptoManager.insert_row(batch, crypto_datum_insert)
            except Exception as e:
                print("Skipped")
                print(e)
            # start_date = end_date

        print("Storing last records...")
        batch.send()
        connection.close()
    except Exception as e:
        print("Cannot open connection\nException: ")
        print(e)

if __name__ == "__main__":
    main()
