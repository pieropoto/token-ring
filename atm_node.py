import socket
import json
import time
import sys
import threading
from datetime import datetime

# Definizione dei nodi
NODES = {
    1: {"ip": "127.0.0.1", "port": 5001, "next": 2},
    2: {"ip": "127.0.0.1", "port": 5002, "next": 3},
    3: {"ip": "127.0.0.1", "port": 5003, "next": 4},
    4: {"ip": "127.0.0.1", "port": 5004, "next": 1},
}


class ATMNode:
    # Inizializzazione dei nodi
    def __init__(self, node_id, is_starter=False):
        self.node_id = node_id
        self.config = NODES[node_id]
        self.next_node = NODES[self.config["next"]]
        self.is_starter = is_starter

        # Variabile di memoria locale per il saldo del conto
        self.local_balance = 1000.0

        self.pending_transaction = None
        self.lock = threading.Lock()

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] [ATM{self.node_id}] {message}")

    def send_message(self, target_ip, target_port, payload):
        """Invia un messaggio TCP JSON a un nodo specifico."""
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((target_ip, target_port))
            client_socket.sendall(json.dumps(payload).encode('utf-8'))
            client_socket.close()
            return True
        except ConnectionRefusedError:
            return False

    def broadcast_balance_update(self, tx_type, amount, new_balance):
        """Invia il messaggio di aggiornamento del saldo a tutti gli altri nodi."""
        update_msg = {
            "type": "BALANCE_UPDATE",
            "sender": f"ATM{self.node_id}",
            "tx_type": tx_type,
            "amount": amount,
            "new_balance": new_balance
        }
        self.log(f"Notifica di aggiornamento saldo in broadcast: Nuovo Saldo = {new_balance} EUR")

        for peer_id, peer_info in NODES.items():
            # Invia a tutti i nodi tranne il mittente
            if peer_id != self.node_id:
                # Tenta l'invio fino a quando il peer non riceve la notifica
                while not self.send_message(peer_info["ip"], peer_info["port"], update_msg):
                    time.sleep(0.5)

    def listen(self):
        """Server TCP in ascolto sia per il TOKEN che per i messaggi BALANCE_UPDATE."""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.config["ip"], self.config["port"]))
        server_socket.listen(10)

        self.log(f"In ascolto sulla porta {self.config['port']}... (Saldo Locale Iniziale: {self.local_balance} EUR)")

        # Se è il nodo starter, immette il token
        if self.is_starter:
            time.sleep(5)  # Attesa per l'avvio manuale dei 4 terminali
            token = {"type": "TOKEN", "owner_history": []}
            self.log(">>> Inizializzazione e immissione del TOKEN nel sistema <<<")
            self.forward_token(token)

        while True:
            conn, _ = server_socket.accept()
            data = conn.recv(1024).decode('utf-8')
            if data:
                message = json.loads(data)

                # Distinzione dei tipi di messaggio
                if message.get("type") == "TOKEN":
                    self.handle_token(message)
                elif message.get("type") == "BALANCE_UPDATE":
                    self.handle_balance_update(message)

            conn.close()

    def handle_balance_update(self, msg):
        """Aggiorna il saldo della memoria locale in seguito a una transazione esterna."""
        with self.lock:
            self.local_balance = msg["new_balance"]
            self.log(
                f" Ricevuta notifica da {msg['sender']}: {msg['tx_type'].upper()} di {msg['amount']} EUR. Saldo locale aggiornato a: {self.local_balance} EUR")

    def handle_token(self, token):
        # Aggiungo una pausa per evitare che i log di questa sezione si sovrappongano all'interfaccia
        # non dando il tempo di inserire le operazioni da eseguire
        time.sleep(5)

        self.log("Ricezione del TOKEN...")

        # Gestione della Sezione Critica
        with self.lock:
            # Se c'è una transazione in coda la esegue, altrimenti invia il token al prossimo nodo
            if self.pending_transaction:
                self.execute_transaction()
                self.pending_transaction = None
            else:
                self.log("Nessuna transazione in coda. Inoltro immediato.")

        # Pausa scenica per evidenziare la circolazione nei log
        time.sleep(2)
        self.forward_token(token)

    def execute_transaction(self):
        self.log("=== INIZIO SEZIONE CRITICA ===")
        # Riconosce il tipo di transazione (deposito o prelievo) e la somma da gestire
        tx_type = self.pending_transaction["type"]
        amount = self.pending_transaction["amount"]

        self.log(f"Lettura saldo locale attuale: {self.local_balance} EUR")
        self.log(f"Esecuzione transazione: {tx_type.upper()} di {amount} EUR")

        # Validazione ed esecuzione sulla memoria locale
        if tx_type == "prelievo":
            # In caso di prelievo, verifica la disponibilità della cifra richiesta
            if self.local_balance >= amount:
                # Aggiorna la variabile locale del bilancio
                self.local_balance -= amount
                self.log(f"Prelievo approvato. Nuovo saldo locale: {self.local_balance} EUR")
                # Propaga l'aggiornamento agli altri nodi
                self.broadcast_balance_update(tx_type, amount, self.local_balance)
            else:
                self.log("ERRORE: Saldo insufficiente per effettuare il prelievo.")
        elif tx_type == "deposito":
            # Aggiorna la variabile locale del bilancio
            self.local_balance += amount
            self.log(f"Deposito effettuato. Nuovo saldo locale: {self.local_balance} EUR")
            # Propaga l'aggiornamento agli altri nodi
            self.broadcast_balance_update(tx_type, amount, self.local_balance)

        self.log("=== FINE SEZIONE CRITICA ===")

    def forward_token(self, token):
        self.log(f"Inoltro del TOKEN a ATM{self.config['next']} ({self.next_node['ip']}:{self.next_node['port']})...")
        while not self.send_message(self.next_node["ip"], self.next_node["port"], token):
            time.sleep(1)

    def user_interface(self):
        """Interfaccia CLI per inviare richieste di transazione."""
        while True:
            print("\n----------------------------------")
            print(f" ATM{self.node_id} - Saldo Locale Attuale: {self.local_balance} EUR")
            print("1. Richiedi Prelievo")
            print("2. Richiedi Deposito")
            print("----------------------------------")
            choice = input("Seleziona un'opzione (1/2): ").strip()

            if choice in ['1', '2']:
                try:
                    amount = float(input("Inserisci l'importo: "))
                    tx_type = "prelievo" if choice == '1' else "deposito"

                    with self.lock:
                        self.pending_transaction = {"type": tx_type, "amount": amount}
                    self.log(
                        f"Transazione ({tx_type} {amount}) accodata. In attesa del TOKEN per entrare in Sezione Critica...")
                except ValueError:
                    print("Importo non valido.")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python atm_node.py <NODE_ID> [--start]")
        sys.exit(1)

    node_id = int(sys.argv[1])
    is_starter = "--start" in sys.argv

    node = ATMNode(node_id, is_starter)

    # Thread separato per il server socket
    server_thread = threading.Thread(target=node.listen, daemon=True)
    server_thread.start()

    # Thread principale per l'interfaccia utente
    node.user_interface()