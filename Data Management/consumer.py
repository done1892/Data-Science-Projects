import datetime
import time
import json
from kafka import KafkaConsumer
from pymongo import MongoClient
import utility


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
    # Imposto le costanti
    DATABASE = default_section.get("mongodb")
    COLLECTION = default_section.get("mongocollection")
    TOPIC = default_section.get("kafka_topic")
    COINS = crypto_section.get("coins")
    HOST = default_section.get("host")
    PORT = default_section.get("kafka_port")
    QUERY_DICT = twitter_section.get("query")

    # Istanzio il DB
    client = MongoClient()
    tweetdb = client[DATABASE]
    print("MongoDB Settings:")
    print("- DB: {}\n- Collection: {}\n".format(DATABASE, COLLECTION))
    # Setto il server
    bootstrap_server = str(HOST) + ":" + str(PORT)
    # Istanzio il Consumer
    print("Setting Consumer")
    try:
        consumer = KafkaConsumer(bootstrap_servers=bootstrap_server,
                                 auto_offset_reset="earliest",
                                 consumer_timeout_ms=1000)
    except Exception as e:
        print("Couldn't start Consumer")
        print("{}\n".format(e.details))
    # Mi iscrivo al topic indicato
    print("Getting topic")
    try:
        consumer.subscribe(TOPIC)
    except Exception as e:
        print("Couldn't subscribe to topic{}".format(TOPIC))
        print("{}\n".format(e.details))

    while(True):
        print("Looking for new tweets")
        for message in consumer:
            print("New tweets sent")
            # Per ogni messaggio arrivato
            try:
                # Decodifico
                dec_message = json.loads(message.value.decode("utf-8"))
                # prendo il corpo del messaggio
                tweet_body = dec_message.get("text")
                # Verifico per quali valute è valido
                for coin in COINS:
                    query = QUERY_DICT.get(coin)
                    if query in tweet_body:
                        # valorizzo il campo coin e scrivo sul DB
                        dec_message["coin"] = coin
                        print("Storing...")
                        tweetdb[COLLECTION].insert_one(dec_message)
            except Exception as e:
                print("Couldn't store tweet\n")
                print("{}\n".format(e.details))
        time.sleep(5)


if __name__ == "__main__":
    main()
