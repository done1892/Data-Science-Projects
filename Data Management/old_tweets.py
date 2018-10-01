import time as t
from itertools import zip_longest
from pymongo import MongoClient
import got3 as got
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
    HOST = default_section.get("host")
    PORT = default_section.get("port")
    START_DATE = default_section.get("start_date").strftime("%Y-%m-%d")
    END_DATE = default_section.get("end_date").strftime("%Y-%m-%d")
    DATABASE = default_section.get("mongodb")
    COLLECTION = default_section.get("mongocollection")
    COINS = crypto_section.get("coins")
    TWEET_STRUCT = twitter_section.get("data_struct_h")
    MAX_TWEETS = twitter_section.get("max_tweets")
    QUERY_DICT = twitter_section.get("query")

    # Istanzio il DB
    client = MongoClient()
    tweetdb = client[DATABASE]
    print("MongoDB Settings:")
    print("- DB: {}\n- Collection: {}\n".format(DATABASE, COLLECTION))
    # Per ciascuna valuta considerata
    TOTAL_tweets = 0
    total_time = 0
    for coin in COINS:
        tweet_list = []
        # Imposto il criterio di ricerca
        print("{} tweets from {} to {}\n".format(coin, START_DATE,
                                                 END_DATE))
        
        query = QUERY_DICT.get(coin)
        if int(MAX_TWEETS) > 0:
            Criterium = got.manager.TweetCriteria().setQuerySearch(
                query).setSince(START_DATE).setUntil(END_DATE).setTopTweets(True).setMaxTweets(
                MAX_TWEETS)
        else:
        # prendo il termine di ricerca corrispondente
            Criterium = got.manager.TweetCriteria().setQuerySearch(
                query).setSince(START_DATE).setUntil(END_DATE).setTopTweets(True)
        # Faccio scraping dei tweet
        print("Scraping...\n")
        download_time = t.monotonic()
        old_tweets = got.manager.TweetManager.getTweets(Criterium)
        elapsed_time = t.monotonic() - download_time
        # calcolo i totali
        # total_tweets += len(old_tweets)
        # total_time += elapsed_time
        #print("{} tweets downloaded in {} s\n".format(total_tweets,
        #                                              elapsed_time))
        # Per ciascun tweet della valuta corrente
        for old_tweet in old_tweets:
            # Valorizzo i campi aggiuntivi
            timestamp = old_tweet.date.timestamp()
            date = str(old_tweet.date.date())
            time = str(old_tweet.date.time())
            created_at = old_tweet.date.strftime("%Y-%m-%d %H:%M:%S")
            # Riempio con tutti i valori
            tweet_values = [old_tweet.username, timestamp, coin, date, time,
                            created_at, old_tweet.text, old_tweet.retweets,
                            old_tweet.hashtags, old_tweet.geo]
            # Unisco la struttura con i suoi valori
            tweet = dict(zip_longest(TWEET_STRUCT, tweet_values))
            # Cancello eventuali valori spaiati
            try:
                del tweet[None]
            except:
                pass
            # Inserisco nella lista da scrivere
            tweet_list.append(tweet)
        try:
            print("Storing records...\n")
            tweetdb[COLLECTION].insert_many(tweet_list)
            print("Records stored successfully! :)\n")
        except BulkWriteError as e:
            print("Couldn't store {} tweets\n".format(coin))
            print("{}\n".format(e.details))
    print("{} tweets download in {} s".format(TOTAL_tweets, total_time))


if __name__ == "__main__":
    main()
