# Data Management

Questo progetto è stato svolto utilizzando l'architettura **Hadoop**.

#

DESCRIZIONE CODICI:

- **config.yaml** e **utility.py**
Dato che l'architettura ideata, prevede di reperire le quotazioni delle cryptovalute e i tweet storici in finestre temporali che possono essere scelte dall'utente, si è optato per
la creazione di un file di configurazione (config.yaml). In tale file è possibile modificare la finestra temporale di ricerca, inoltre abbiamo inserito tutti i valori necessari
al codice per funzionare: l'host, le porte kafka, le chiavi di accesso per le api di twitter, le parole chiave per la ricerca di tweepy, la grandezza del batch di hbase ecc.
Tutti questi valori sono modificabili, diventa dunque semplice cambiare topic di kafka in cui scrivere e leggere i messaggi, oppure scegliere un'altra collezione o db di mongodb, senza
dover modificare il codice.
Il file utility.py è necessario per aprire il file di configurazione config.yaml

- **producer.py** e **consumer.py**
Parte dei dati che abbiamo catturato arrivano da twitter e riguardano informazioni sul testo di alcuni tweet pubblicati in tempo reale e alcune informazioni sull'utente che ha pubblicato
tale tweet. A tal fine ci siamo serviti della libreria tweepy, e per lo streaming ci siamo serviti di Kafta, tool dell'ecosistema Hadoop. Tramite il producer trasferiamo i tweet e le
relative informazioni ad un topic; il consumer accede al topic, reperisce i dati sui tweet e li storicizza in Mongodb. Viene effettuato anche un controllo sulla semantica del testo del tweet:
esso deve contenere almeno una parola della lista query nel file config.yaml

- **old_tweets.py**
Tramite questo codice accediamo ai dati relativi a tweet indietro nel tempo, tramite scraping. Modificando la finestra temporale e la parola chiave di ricerca nel file di configurazione, lo script andrà a
cercare i tweet secondo tali richieste. Infine, sempre tramite pymongo, i tweet vengono scritti su Mongodb; il nome della collezione e del db vanno anch'essi definiti nel file di
configurazione, che lo script andrà a leggere in fase di inizializzazione delle variabili.

- **Crypto_currencies.py**
Questo script ha il compito di reperire le crypto quotazioni e di storarle su HBase. Le quotazioni vengono catturate grazie alle API di POLONIEX, una piattaforma di scambio cryptovalute.
Successivamente, tramite la libreria happybase, le quotazioni vengono storate su HBase, nella tabella crypto_quotations. Le righe vengono raggruppate in batch, prima di essere inviate e caricate
su Hbase, in quanto si riduce il tempo di invio e scrittura su db.
