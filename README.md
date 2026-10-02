# token-ring
Il token viene iniettato nel nodo 1 e circola in ordine 1-2-3-4-1
Le transazioni inserite restano in attesa fino all'arrivo del token in quel nodo
All'arrivo del token, se ci sono transazioni in attesa vengono eseguite, altrimenti il token viene direttamente inoltrato al nodo successivo
Ogni volta che viene eseguita una transazione e quindi aggiornato il bilancio locale di quel nodo, gli altri nodi vengono notificati della transazione avvenuta per aggiornare le proprie variabili locali del bilancio.
