import datetime
from itertools import zip_longest
import json
import time
from kafka import KafkaProducer
import tweepy
from tweepy import OAuthHandler
from tweepy import Stream
import utility


class Listener(tweepy.StreamListener):
    """Custom listener implementation"""

    def __init__(self, tweet_struct, producer, topic):
        self.tweet_struct = tweet_struct
        self.producer = producer
        self.topic = topic
        super().__init__()

    def on_status(self, status):
        """ """
        # Costruisco il tweet
        # Valorizzo i campi aggiuntivi
        timestamp = status.created_at.timestamp()
        coin = ""
        date = str(status.created_at.date())
        time = str(status.created_at.time())
        created_at = status.created_at.strftime("%Y-%m-%d %H:%M:%S")
        # Riempio con tutti i valori
        tweet_values = [status.user.name, timestamp, coin, date, time,
                        created_at, status.text, status.retweet_count,
                        status.entities["hashtags"], status.user.lang,
                        status.user.followers_count,
                        status.user.friends_count, status.user.location]
        # Unisco la struttura con i suoi valori
        tweet = dict(zip_longest(self.tweet_struct, tweet_values))
        # Cancello eventuali valori spaiati
        try:
            del tweet[None]
        except:
            pass
        # lo invio sul topic definito dopo averlo convertito in json
        self.producer.send(self.topic, json.dumps(tweet).encode("utf-8"))

    def on_error(self, status_code):
        """ Error Management"""

        print("Error code: {}".format(status_code))
        if status_code == 420:
            # Con false disconnettiamo
            return False
        else:
            return True


def main():
    # Carico la configurazione
    CONFIG_FILE_PATH = "config.yaml"
    print("\nGetting {} as configuration file\n".format(CONFIG_FILE_PATH))
    config_helper = utility.ConfigHelper(CONFIG_FILE_PATH)
    config = config_helper.get_configuration()
    # Carico le sezioni necessarie
    default_section = config.get("default")
    twitter_section = config.get("twitter")
    # Definisco le costanti
    HOST = default_section.get("host")
    PORT = default_section.get("kafka_port")
    TOPIC = default_section.get("kafka_topic")
    CONSUMER_KEY = twitter_section.get("consumer_key")
    CONSUMER_SECRET = twitter_section.get("consumer_secret")
    ACCESS_TOKEN = twitter_section.get("access_token")
    ACCESS_TOKEN_SECRET = twitter_section.get("access_token_secret")
    TWEET_STRUCT = twitter_section.get("data_struct_s")
    QUERY_DICT = twitter_section.get("query")
    QUERY = list(QUERY_DICT.values())
    # Setto il server
    bootstrap_server = str(HOST) + ":" + str(PORT)
    # Istanzio il Producer
    print("Setting Producer")
    try:
        producer = KafkaProducer(bootstrap_servers=bootstrap_server,
                                 api_version=(0, 10))
    except Exception as e:
        print("Couldn't start Producer\n")
        print("{}\n".format(e.details))
    # Creo gli oggetti per le autorizzazioni
    print("Authenticating...")
    try:
        auth = OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
        auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
        api = tweepy.API(auth)
    except Exception as e:
        print("Couldn't authenticate on Twitter\n")
        print("{}\n".format(e.details))
    # Istanzio la classe Listener
    streamListener = Listener(TWEET_STRUCT, producer, TOPIC)
    # Creo lo stream
    print("Setting Streamer")
    try:
        stream = Stream(auth=api.auth, listener=streamListener)
    except Exception as e:
        print("Couldn't build the Streamer\n")
        print("{}\n".format(e.details))
    # Filtro
    print("Stream flowing...")
    try:
        stream.filter(track=QUERY, languages=["en"])
    except Exception as e:
        print("Error on streaming\n")
        print("{}\n".format(e.details))


if __name__ == "__main__":
    main()
