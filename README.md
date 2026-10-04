# token-ring
1.Istruzioni di Esecuzione

1.1 Linguaggio e Requisiti di Sistema

Linguaggio di Programmazione: Python 3 (versione 3.8 o superiore).
Dipendenze e Librerie: Nessuna dipendenza di terze parti richiesta. Il sistema utilizza esclusivamente le librerie standard di Python (socket, json, threading, sys, time, datetime). L’unico requisito è installare python.
Modalità di Compilazione: Python è un linguaggio interpretato, non richiede una fase di compilazione.

1.2 Mappatura dei Nodi-Terminali
Ciascuno dei 4 nodi simula un bancomat (ATM) indipendente con il proprio processo autonomo eseguito in un terminale dedicato su localhost (127.0.0.1).
L'anello logico per il passaggio del Token è configurato come segue:

Terminale	  Nodo ATM       	Indirizzo IP	Porta  TCP	 Successore Logico	 Saldo Iniziale
Terminal 1	ATM1 (Starter)	127.0.0.1	    5001	 ATM2      (5002)	           1000 EUR
Terminal 2	ATM2	          127.0.0.1	    5002	 ATM3      (5003)	           1000 EUR
Terminal 3	ATM3	          127.0.0.1	    5003	 ATM4      (5004)	           1000 EUR
Terminal 4	ATM4	          127.0.0.1	    5004	 ATM1      (5001)	           1000 EUR

1.3 Procedura di Avvio e Comandi Esatti
Per garantire l'avvio corretto della rete socket e della circolazione del Token, aprire 4 finestre di terminale separate, posizionarsi nella cartella di progetto token-ring (contenente il file scaricato da github atm_node.py) ed eseguire i comandi nell'ordine indicato:

Fase 1: Avvio dei Nodi Passivi (In ascolto)
Avviare prima i nodi dal 2 al 4 per mettere i relativi server TCP in ascolto sulle rispettive porte  (il numero alla fine del comando indica il terminale: 2 per ATM2, 3 per ATM3 e così via):

Terminal 2 (ATM2):
macOS / Linux: python3 atm_node.py 2
Windows: python atm_node.py 2 (oppure py atm_node.py 2)

Terminal 3 (ATM3):
macOS / Linux: python3 atm_node.py 3
Windows: python atm_node.py 3 (oppure py atm_node.py 3)

Terminal 4 (ATM4):
macOS / Linux: python3 atm_node.py 4
Windows: python atm_node.py 4 (oppure py atm_node.py 4)

Fase 2: Avvio del Nodo Inizializzatore (Starter)
Avviare il Nodo 1 specificando il flag --start. Il nodo attenderà 5 secondi per consentire l'assestamento della rete e poi immetterà il primo Token nell'anello:

Terminal 1 (ATM1 - Starter):
macOS / Linux: python3 atm_node.py 1 --start
Windows: python atm_node.py 1 --start (oppure py atm_node.py 1 --start)

Inserimento transazioni
All’avvio del nodo si apre un’nterfaccia in cui viene richiesto di scegliere un tipo di transazione: 1 per il prelievo, 2 per il deposito. Dopo questa scelta viene chiesta la cifra: inserire il valore numerico. Per far apparire di nuovo l’interfaccia e interagire con il nodo ATM durante la circolazione dei log basta remere invio.

1.4 Spiegazione Funzionale
Isolamento della Memoria: Ogni terminale esegue un'istanza autonoma dell'interprete Python. Ciò garantisce che la variabile local_balance (inizializzata a 1000 EUR) sia strettamente privata a ciascun processo e che non vi sia alcuna memoria condivisa diretta tra gli ATM.
Coordinamento e Sezione Critica: L'accesso al conto per prelievi o depositi avviene solo dopo la ricezione del messaggio TOKEN inviato su socket TCP dal nodo precedente. All'arrivo del token, se ci sono transazioni in attesa vengono eseguite, altrimenti il token viene direttamente inoltrato al nodo successivo.
Broadcast delle Transazioni: All'esecuzione di una transazione in Sezione Critica, il nodo invia un messaggio BALANCE_UPDATE agli altri 3 nodi per allineare le loro variabili locali di saldo in modo distribuito.
