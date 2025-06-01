import random
import sys
import os
import sqlite3 # Added for SQLite
import datetime # Added for timestamping

# Database setup
DB_NAME = "queue.db"

# Pragul de timp (în secunde) după care prioritatea unui client crește automat
MAX_WAIT_TIME_SECONDS_BEFORE_BUMP = 120  # 2 minute (2 * 60)

# Store closing mode - when True, no new clients are accepted
store_closing_mode = False

# Auto serving mode - when True, clients are served automatically
auto_serving_mode = False

# Heap mode - True for max-heap (highest priority first), False for min-heap (lowest priority first)
# Note: In this system, lower numbers = higher priority, so:
# max_heap_mode = True means serve clients with LOWER priority numbers first (higher priority)
# max_heap_mode = False means serve clients with HIGHER priority numbers first (lower priority)
max_heap_mode = True  # Default to max-heap (serve highest priority first)

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_name TEXT NOT NULL,
            priority_level INTEGER NOT NULL,
            serving_time INTEGER NOT NULL,
            added_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

if os.name == 'nt': 
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        print("Warning: Could not reconfigure stdout/stderr for UTF-8 automatically. Special characters might not display correctly. Consider running in a UTF-8 compatible terminal or setting PYTHONIOENCODING=UTF-8.", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred while trying to reconfigure stdout/stderr: {e}", file=sys.stderr)


# Şanse de generare şi Priorități pentru fiecare tip client
client_types = {
    'urgenta': 1,
    'client_cu_dizabilitati': 3,
    'familie_cu_dizabilitati': 5,
    'familie_cu_copii': 12,
    'client_cu_abonament': 15,
    'mama_insarcinata': 7,
    'angajatii': 4,
    'client_fara_abonament': 53
}

client_priorities = {
    'urgenta': (1, 15),  # (prioritate, timp_servire_secunde - valoare tipică/medie)
    'client_cu_dizabilitati': (2, 20),
    'familie_cu_dizabilitati': (3, 25),
    'familie_cu_copii': (4, 18),
    'client_cu_abonament': (5, 15),
    'mama_insarcinata': (6, 20),
    'angajatii': (7, 10),
    'client_fara_abonament': (8, 12)
}

def get_client_type_for_priority(prio_level):
    """Returnează tipul de client corespunzător unei priorități date."""
    for client_type, (p, _) in client_priorities.items():
        if p == prio_level:
            return client_type
    return None # Sau un tip de client implicit/de rezervă

def generator_for_priority(prio_level, count):
    # Generează 'count' număr de clienți pentru o prioritate dată
    clients = []
    for _ in range(count):
        client_name = None
        # client_serving_time este acum generat random între 5 și 30 secunde
        client_serving_time = random.randint(5, 30) 
        for name, (p, _) in client_priorities.items(): # Ignorăm timpul din client_priorities aici
            if p == prio_level:
                client_name = name
                break
        if client_name is None:
            continue  # ignoră dacă nu găsește
        clients.append((client_name, prio_level, client_serving_time))
    return clients

def afisare_coada():
    heap_mode_desc = "crescător după prioritate (MAX-HEAP)" if max_heap_mode else "descrescător după prioritate (MIN-HEAP)"
    print(f"\\nStarea curentă a cozii (ordonată {heap_mode_desc}):")
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Order based on heap mode: max_heap_mode=True means ascending (higher priority first), False means descending
    order_direction = "ASC" if max_heap_mode else "DESC"
    cursor.execute(f"SELECT client_name, priority_level, serving_time, added_timestamp FROM clients ORDER BY priority_level {order_direction}, added_timestamp")
    clients_in_db = cursor.fetchall()
    conn.close()

    if not clients_in_db:
        print("Coada este goală.")
        return
    
    cumulative_eta = 0
    for idx, client_row in enumerate(clients_in_db, 1):
        # Use serving_time directly instead of cumulative ETA
        # Modificăm formatul de afișare pentru a include și added_timestamp și unitatea 's'
        print(f"{idx}. {client_row['client_name']} - Prio: {client_row['priority_level']} (Serv: {client_row['serving_time']}s) Adăugat: {client_row['added_timestamp']} - ETA start: {client_row['serving_time']}s")
        cumulative_eta += client_row['serving_time']
    print(f"Timp total estimat pentru golirea cozii: {cumulative_eta} secunde.")

def filter_clients_by_index(start_index=None, end_index=None):
    """Filtrează clienții după index (poziția în coadă)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Order based on heap mode: max_heap_mode=True means ascending (higher priority first), False means descending
    order_direction = "ASC" if max_heap_mode else "DESC"
    cursor.execute(f"SELECT id, client_name, priority_level, serving_time, added_timestamp FROM clients ORDER BY priority_level {order_direction}, added_timestamp")
    all_clients = cursor.fetchall()
    conn.close()
    
    if not all_clients:
        print("Coada este goală.")
        return []
    
    total_clients = len(all_clients)
    
    if start_index is None:
        start_index = 1
    if end_index is None:
        end_index = total_clients
        
    # Validare index
    if start_index < 1 or start_index > total_clients:
        print(f"Index de start invalid. Trebuie să fie între 1 și {total_clients}.")
        return []
    if end_index < 1 or end_index > total_clients:
        print(f"Index de sfârșit invalid. Trebuie să fie între 1 și {total_clients}.")
        return []
    if start_index > end_index:
        print("Index de start nu poate fi mai mare decât index de sfârșit.")
        return []
    
    filtered_clients = all_clients[start_index-1:end_index]
    return filtered_clients

def filter_clients_by_priority(priority_levels=None):
    """Filtrează clienții după nivele de prioritate specifice."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Order based on heap mode: max_heap_mode=True means ascending (higher priority first), False means descending
    order_direction = "ASC" if max_heap_mode else "DESC"
    
    if priority_levels is None or not priority_levels:
        # Dacă nu sunt specificate priorități, returnează toți clienții
        cursor.execute(f"SELECT id, client_name, priority_level, serving_time, added_timestamp FROM clients ORDER BY priority_level {order_direction}, added_timestamp")
    else:
        # Construiește query pentru prioritățile specificate
        placeholders = ','.join('?' * len(priority_levels))
        query = f"SELECT id, client_name, priority_level, serving_time, added_timestamp FROM clients WHERE priority_level IN ({placeholders}) ORDER BY priority_level {order_direction}, added_timestamp"
        cursor.execute(query, priority_levels)
    
    filtered_clients = cursor.fetchall()
    conn.close()
    return filtered_clients

def filter_clients_by_serving_time(min_time=None, max_time=None):
    """Filtrează clienții după timpul de servire (în secunde)."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    conditions = []
    params = []
    
    if min_time is not None:
        conditions.append("serving_time >= ?")
        params.append(min_time)
    
    if max_time is not None:
        conditions.append("serving_time <= ?")
        params.append(max_time)
    
    # Order based on heap mode: max_heap_mode=True means ascending (higher priority first), False means descending
    order_direction = "ASC" if max_heap_mode else "DESC"
    
    if conditions:
        where_clause = "WHERE " + " AND ".join(conditions)
        query = f"SELECT id, client_name, priority_level, serving_time, added_timestamp FROM clients {where_clause} ORDER BY priority_level {order_direction}, added_timestamp"
        cursor.execute(query, params)
    else:
        cursor.execute(f"SELECT id, client_name, priority_level, serving_time, added_timestamp FROM clients ORDER BY priority_level {order_direction}, added_timestamp")
    
    filtered_clients = cursor.fetchall()
    conn.close()
    return filtered_clients

def display_filtered_clients(clients, filter_description=""):
    """Afișează clienții filtrați."""
    if not clients:
        print(f"Nu există clienți care să corespundă filtrului {filter_description}.")
        return
    
    print(f"\\nClienți filtrați {filter_description}:")
    print("-" * 80)
    cumulative_eta = 0
    for idx, client in enumerate(clients, 1):
        # Use serving_time directly instead of cumulative ETA
        print(f"{idx}. {client['client_name']} - Prio: {client['priority_level']} (Serv: {client['serving_time']}s) Adăugat: {client['added_timestamp']} - ETA start: {client['serving_time']}s")
        cumulative_eta += client['serving_time']
    print(f"Timp total estimat pentru clienții filtrați: {cumulative_eta} secunde.")

def toggle_store_closing_mode():
    """Comută modul de închidere magazin."""
    global store_closing_mode
    store_closing_mode = not store_closing_mode
    status = "ACTIVAT" if store_closing_mode else "DEZACTIVAT"
    print(f"Modul închidere magazin: {status}")
    if store_closing_mode:
        print("⚠️  Nu se mai acceptă clienți noi!")
    else:
        print("✅ Se acceptă clienți noi.")
    return store_closing_mode

def toggle_auto_serving_mode():
    """Comută modul de servire automată."""
    global auto_serving_mode
    auto_serving_mode = not auto_serving_mode
    status = "ACTIVAT" if auto_serving_mode else "DEZACTIVAT"
    print(f"Modul servire automată: {status}")
    if auto_serving_mode:
        print("🤖 Servirea automată a fost activată!")
    else:
        print("✋ Servirea automată a fost oprită.")
    return auto_serving_mode

def toggle_heap_mode():
    """Comută modul de servire între max-heap și min-heap."""
    global max_heap_mode
    max_heap_mode = not max_heap_mode
    mode_name = "MAX-HEAP (prioritate înaltă primul)" if max_heap_mode else "MIN-HEAP (prioritate joasă primul)"
    print(f"Modul de servire schimbat la: {mode_name}")
    if max_heap_mode:
        print("🔺 Clienții cu prioritatea cea mai înaltă (numărul cel mai mic) vor fi serviți primul!")
    else:
        print("🔻 Clienții cu prioritatea cea mai joasă (numărul cel mai mare) vor fi serviți primul!")
    return max_heap_mode

def auto_serve_clients(current_simulated_time):
    """Servește clienții automat până când este oprit sau rămâne un singur client."""
    global auto_serving_mode
    
    if not auto_serving_mode:
        print("Modul de servire automată nu este activat.")
        return current_simulated_time
    
    print("🤖 Începe servirea automată...")
    print("Apăsați Enter pentru a opri servirea automată.")
    
    import threading
    import time
    
    # Flag pentru a opri servirea automată
    stop_auto_serving = threading.Event()
    
    def check_for_stop():
        input()  # Așteaptă ca utilizatorul să apese Enter
        stop_auto_serving.set()
    
    # Pornește thread-ul pentru a verifica dacă utilizatorul vrea să oprească
    stop_thread = threading.Thread(target=check_for_stop, daemon=True)
    stop_thread.start()
    
    clients_served = 0
    
    while auto_serving_mode and not stop_auto_serving.is_set():
        # Verifică câți clienți sunt în coadă
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM clients")
        client_count = cursor.fetchone()[0]
        conn.close()
        
        if client_count <= 1:
            print(f"\n✅ Servirea automată s-a oprit: {'rămâne un singur client' if client_count == 1 else 'coada este goală'}.")
            auto_serving_mode = False
            break
        
        # Servește următorul client
        print(f"\n--- Servind automat clientul #{clients_served + 1} ---")
        current_simulated_time = serve_next(current_simulated_time)
        clients_served += 1
        
        # Afișează starea cozii după fiecare client servit
        afisare_coada()
        
        # Pauză scurtă pentru a permite utilizatorului să vadă progresul
        time.sleep(0.5)
        
        # Verifică din nou dacă utilizatorul a apăsat Enter
        if stop_auto_serving.is_set():
            break
    
    if stop_auto_serving.is_set():
        print(f"\n✋ Servirea automată a fost oprită de utilizator după {clients_served} clienți serviți.")
        auto_serving_mode = False
    
    return current_simulated_time

def filter_menu():
    """Meniu pentru opțiunile de filtrare."""
    while True:
        print("\\n=== MENIU FILTRARE ===")
        print("[1] Filtrare după Index")
        print("[2] Filtrare după Prioritate") 
        print("[3] Filtrare după Timp Servire")
        print("[B] Înapoi la meniul principal")
        
        choice = input("Alegeți o opțiune: ").strip().lower()
        
        if choice == '1':
            filter_by_index_menu()
        elif choice == '2':
            filter_by_priority_menu()
        elif choice == '3':
            filter_by_serving_time_menu()
        elif choice == 'b':
            break
        else:
            print("Opțiune invalidă, vă rog încercați din nou.")

def filter_by_index_menu():
    """Meniu pentru filtrarea după index."""
    try:
        print("\\nFiltrare după index (poziția în coadă)")
        start_idx = input("Index de start (apăsați Enter pentru 1): ").strip()
        end_idx = input("Index de sfârșit (apăsați Enter pentru ultimul): ").strip()
        
        start_index = int(start_idx) if start_idx else None
        end_index = int(end_idx) if end_idx else None
        
        filtered = filter_clients_by_index(start_index, end_index)
        display_filtered_clients(filtered, f"(index {start_index or 1} - {end_index or 'sfârșit'})")
    except ValueError:
        print("Vă rugăm să introduceți numere valide pentru index.")

def filter_by_priority_menu():
    """Meniu pentru filtrarea după prioritate."""
    try:
        print("\\nFiltrare după prioritate")
        print("Introduceți prioritățile dorite separate prin virgulă (ex: 1,3,5)")
        print("Sau apăsați Enter pentru toate prioritățile")
        prio_input = input("Priorități: ").strip()
        
        if prio_input:
            priority_levels = [int(p.strip()) for p in prio_input.split(',')]
            # Validare priorități
            invalid_prios = [p for p in priority_levels if p < 1 or p > 8]
            if invalid_prios:
                print(f"Priorități invalide: {invalid_prios}. Folosiți valori între 1-8.")
                return
        else:
            priority_levels = None
        
        filtered = filter_clients_by_priority(priority_levels)
        prio_desc = f"(priorități: {','.join(map(str, priority_levels))})" if priority_levels else "(toate prioritățile)"
        display_filtered_clients(filtered, prio_desc)
    except ValueError:
        print("Vă rugăm să introduceți numere valide pentru priorități.")

def filter_by_serving_time_menu():
    """Meniu pentru filtrarea după timpul de servire."""
    try:
        print("\\nFiltrare după timpul de servire (secunde)")
        min_time_input = input("Timp minim (apăsați Enter pentru fără limită): ").strip()
        max_time_input = input("Timp maxim (apăsați Enter pentru fără limită): ").strip()
        
        min_time = int(min_time_input) if min_time_input else None
        max_time = int(max_time_input) if max_time_input else None
        
        if min_time is not None and min_time < 0:
            print("Timpul minim nu poate fi negativ.")
            return
        if max_time is not None and max_time < 0:
            print("Timpul maxim nu poate fi negativ.")
            return
        if min_time is not None and max_time is not None and min_time > max_time:
            print("Timpul minim nu poate fi mai mare decât timpul maxim.")
            return
        
        filtered = filter_clients_by_serving_time(min_time, max_time)
        time_desc = f"(timp servire: {min_time or 0}s - {max_time or '∞'}s)"
        display_filtered_clients(filtered, time_desc)
    except ValueError:
        print("Vă rugăm să introduceți numere valide pentru timp.")

def adauga_clienti_bundle(current_simulated_time): # Added current_simulated_time
    # Verifică modul de închidere magazin
    if store_closing_mode:
        print("⚠️  Magazinul este în modul de închidere! Nu se mai acceptă clienți noi.")
        return
        
    while True:
        try:
            prio_level = int(input("Introduceți prioritatea clienților de adăugat (1-8): "))
            if not 1 <= prio_level <= 8:
                print("Prioritatea trebuie să fie între 1 și 8.")
                continue
            
            valid_prio = False
            client_name_for_prio, serving_time_for_prio = None, None
            for name, (p, t) in client_priorities.items():
                if p == prio_level:
                    valid_prio = True
                    client_name_for_prio = name # We need a representative name for this prio
                    serving_time_for_prio = t
                    break 
            if not valid_prio:
                print(f"Nu există un tip de client definit pentru prioritatea {prio_level}.")
                continue

            count = int(input("Câți clienți doriți să adăugați? "))
            if count < 1:
                print("Numărul trebuie să fie cel puțin 1.")
                continue
            
            # The generator_for_priority helps find the client_name and serving_time
            # for the given prio_level. We'll use the first one it finds.
            clients_to_add_data = generator_for_priority(prio_level, count)

            if not clients_to_add_data:
                print("Prioritate invalidă sau nu s-au putut genera datele clienților.")
                continue
            
            conn = get_db_connection()
            cursor = conn.cursor()
            for c_name, c_prio, c_time in clients_to_add_data:
                cursor.execute("INSERT INTO clients (client_name, priority_level, serving_time, added_timestamp) VALUES (?, ?, ?, ?)",
                               (c_name, c_prio, c_time, current_simulated_time)) # Use current_simulated_time
            conn.commit()
            conn.close()
            
            print(f"{count} clienți cu prioritatea {prio_level} au fost adăugați în baza de date (la timpul simulat).") # Updated print
            break
        except ValueError:
            print("Vă rugăm să introduceți un număr valid.")

def sterge_clienti_bundle():
    while True:
        try:
            prio_level = int(input("Introduceți prioritatea clienților pe care doriți să-i ștergeți (1-8): "))
            if prio_level < 1 or prio_level > 8:
                print("Prioritatea trebuie să fie între 1 și 8.")
                continue

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM clients WHERE priority_level = ?", (prio_level,))
            clients_to_delete = cursor.fetchall()
            numar_gasiti = len(clients_to_delete)
            
            if numar_gasiti == 0:
                print(f"Nu există clienți cu prioritatea {prio_level} în coadă.")
                return
            print(f"Există {numar_gasiti} clienți cu prioritatea {prio_level} în coadă.")

            count = int(input("Câți clienți doriți să ștergeți? "))
            if count < 1:
                print("Numărul trebuie să fie cel puțin 1.")
                continue
            if count > numar_gasiti:
                print(f"Nu puteți șterge {count} clienți deoarece există doar {numar_gasiti} cu prioritatea {prio_level}.")
                print("Vă rugăm să introduceți un număr mai mic sau egal cu cel disponibil.")
                continue

            # Ștergem clienții din baza de date
            for i in range(count):
                client_id = clients_to_delete[i]['id']
                cursor.execute("DELETE FROM clients WHERE id = ?", (client_id,))
            
            conn.commit()
            conn.close()
            print(f"{count} clienți cu prioritatea {prio_level} au fost șterși cu succes.")
            break
        except ValueError:
            print("Vă rugăm să introduceți un număr valid.") # Eroarea

def serve_next(current_simulated_time): # Adăugăm current_simulated_time ca parametru
    conn = get_db_connection()
    cursor = conn.cursor()

    # Order based on heap mode: max_heap_mode=True means ascending (higher priority first), False means descending
    order_direction = "ASC" if max_heap_mode else "DESC"
    cursor.execute(f"SELECT id, client_name, priority_level, serving_time FROM clients ORDER BY priority_level {order_direction}, added_timestamp LIMIT 1")
    client_to_serve = cursor.fetchone()

    if client_to_serve is None:
        print("Coada este goală. Nu există clienți de servit.")
        return current_simulated_time # Returnăm timpul nemodificat
    
    client_id_to_serve = client_to_serve['id']
    serving_time_seconds = client_to_serve['serving_time']

    # Ștergem clientul din baza de date (servirea lui)
    cursor.execute("DELETE FROM clients WHERE id = ?", (client_id_to_serve,))
    conn.commit()

    print(f"Clientul '{client_to_serve['client_name']}' cu prioritatea {client_to_serve['priority_level']} (timp servire: {serving_time_seconds}s) a fost servit.")
    
    # Avansăm timpul simulat cu timpul de servire al clientului
    new_simulated_time = current_simulated_time + datetime.timedelta(seconds=serving_time_seconds)
    print(f"Timpul simulat a avansat cu {serving_time_seconds}s la {new_simulated_time.strftime('%Y-%m-%d %H:%M:%S')}.")
    
    # Adăugăm un client nou doar dacă magazinul nu este în modul de închidere
    if not store_closing_mode:
        types_available = list(client_types.keys()) 
        weights = list(client_types.values())
        selected_client_type_name = random.choices(types_available, weights=weights, k=1)[0]
        prio_level, _ = client_priorities[selected_client_type_name]
        serving_time = random.randint(5, 30)
        
        cursor.execute("INSERT INTO clients (client_name, priority_level, serving_time, added_timestamp) VALUES (?, ?, ?, ?)",
                       (selected_client_type_name, prio_level, serving_time, new_simulated_time))
        conn.commit()
        
        print(f"Un client nou '{selected_client_type_name}' cu prioritatea {prio_level} a fost adăugat în coadă (timp servire: {serving_time}s).")
    else:
        print("Magazinul este în modul de închidere - nu se adaugă clienți noi.")
    
    conn.close()
    return new_simulated_time # Returnăm noul timp simulat

def update_priority():
    while True:
        try:
            current_prio_level = int(input("Introduceți prioritatea curentă a clienților pe care doriți să-i actualizați (1-8): "))
            if not 1 <= current_prio_level <= 8:
                print("Prioritatea trebuie să fie între 1 și 8.")
                continue

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, client_name, priority_level, serving_time FROM clients WHERE priority_level = ?", (current_prio_level,))
            clients_with_current_prio = cursor.fetchall()
            num_found = len(clients_with_current_prio)

            if num_found == 0:
                print(f"Nu există clienți cu prioritatea {current_prio_level} în coadă.")
                return
            
            print(f"Există {num_found} clienți cu prioritatea {current_prio_level} în coadă.")

            count_to_update = int(input(f"Câți clienți cu prioritatea {current_prio_level} doriți să actualizați? "))
            if count_to_update < 1:
                print("Numărul trebuie să fie cel puțin 1.")
                continue
            if count_to_update > num_found:
                print(f"Nu puteți actualiza {count_to_update} clienți deoarece există doar {num_found} cu prioritatea {current_prio_level}.")
                print("Vă rugăm să introduceți un număr mai mic sau egal cu cel disponibil.")
                continue

            new_prio_val = int(input(f"Introduceți noua prioritate pentru acești {count_to_update} clienți (1-8): "))
            if not 1 <= new_prio_val <= 8:
                print("Noua prioritate trebuie să fie între 1 și 8.")
                continue
            
            # Verificăm dacă noua prioritate are un tip de client definit (și implicit un timp de servire)
            new_serving_time_for_new_prio = None
            new_client_type_for_new_prio = None
            for c_type, (p, t) in client_priorities.items():
                if p == new_prio_val:
                    # Teoretic, ar trebui să actualizăm și tipul clientului dacă prioritatea se schimbă
                    # Dar pentru a păstra timpul de servire original, vom ignora timpul de servire al noii priorități
                    # și vom păstra timpul de servire original al clientului.
                    # Dacă am dori să preluăm noul timp de servire, am face: new_serving_time_for_new_prio = t
                    new_client_type_for_new_prio = c_type # Să presupunem că tipul se schimbă cu prioritatea
                    break 
            
            if new_client_type_for_new_prio is None:
                 print(f"Noua prioritate {new_prio_val} nu corespunde unui tip de client valid. Actualizare anulată.")
                 continue


            updated_count = 0
            for i in range(count_to_update):
                client_row = clients_with_current_prio[i]
                client_id = client_row['id']
                client_name = client_row['client_name']
                original_serving_time = client_row['serving_time'] # Păstrăm timpul de servire original
                
                # Găsim noul nume de client corespunzător noii priorități
                # Aceasta este o simplificare; ideal, ar trebui să întrebăm ce tip de client devine.
                # Pentru acest exemplu, vom lua primul tip de client care are noua prioritate.
                new_client_name_for_new_prio = client_name # Default to old name if no type matches new prio
                for c_type_key, (p_val, _) in client_priorities.items():
                    if p_val == new_prio_val:
                        new_client_name_for_new_prio = c_type_key
                        break

                cursor.execute("UPDATE clients SET client_name = ?, priority_level = ? WHERE id = ?",
                               (new_client_name_for_new_prio, new_prio_val, client_id))
                updated_count += 1
            
            conn.commit()
            conn.close()
            print(f"{updated_count} clienți au fost actualizați la prioritatea {new_prio_val} (păstrând timpii de servire originali în secunde).")
            break
        except ValueError:
            print("Vă rugăm să introduceți un număr valid.")
        except Exception as e:
            print(f"A apărut o eroare neașteptată: {e}")
            break

def calculate_eta_for_client():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Order based on heap mode: max_heap_mode=True means ascending (higher priority first), False means descending
    order_direction = "ASC" if max_heap_mode else "DESC"
    cursor.execute(f"SELECT id, client_name, priority_level, serving_time FROM clients ORDER BY priority_level {order_direction}, added_timestamp")
    all_clients_ordered = cursor.fetchall()

    if not all_clients_ordered:
        print("Coada este goală. Nu se poate calcula ETA.")
        return
    
    while True:
        try:
            position = int(input(f"Introduceți poziția clientului în coadă (1-{len(all_clients_ordered)}): "))
            if not 1 <= position <= len(all_clients_ordered):
                print(f"Poziția trebuie să fie între 1 și {len(all_clients_ordered)}.")
                continue

            eta_att = 0
            for i in range(position - 1): # Timpul de așteptare până la clientul din față
                eta_att += all_clients_ordered[i]['serving_time'] # Adunăm timpul de servire al fiecărui client din față
            
            client_la_pozitie = all_clients_ordered[position-1]
            timp_servire_client = client_la_pozitie['serving_time']
            eta_finalizare_client = eta_att + timp_servire_client

            print(f"Clientul '{client_la_pozitie['client_name']}' (Prioritate {client_la_pozitie['priority_level']}) la poziția {position}:")
            print(f"  - Timp estimat de așteptare până la servire: {eta_att} secunde.")
            print(f"  - Timp estimat de servire propriu-zis: {timp_servire_client} secunde.")
            print(f"  - ETA finalizare servire: {eta_finalizare_client} secunde de la momentul actual.")
            break
        except ValueError:
            print("Vă rugăm să introduceți un număr valid pentru poziție.")
        except IndexError: # Ar trebui acoperit de validarea poziției
            print("Poziție invalidă.")
            break

def adaptive_priority_adjustment(current_simulated_time): # Added current_simulated_time
    """Ajustează prioritatea clienților care așteaptă prea mult timp."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Obținem timpul curent simulat
    now = current_simulated_time # Use passed simulated time

    cursor.execute("SELECT id, client_name, priority_level, added_timestamp FROM clients WHERE priority_level > 1 ORDER BY added_timestamp")
    clients_to_check = cursor.fetchall()

    updated_clients_count = 0

    for client in clients_to_check:
        try:
            added_time_str = client['added_timestamp']
            # Simplificăm parsarea folosind direct fromisoformat
            added_time = datetime.datetime.fromisoformat(added_time_str)
        except (ValueError, TypeError) as e: # Adăugat TypeError pentru cazul în care added_timestamp este None sau alt tip neașteptat
            print(f"Warning: Could not parse timestamp '{added_time_str}' for client ID {client['id']}. Error: {e}. Skipping this client for priority adjustment.")
            continue

        wait_duration_seconds = (now - added_time).total_seconds()

        if wait_duration_seconds > MAX_WAIT_TIME_SECONDS_BEFORE_BUMP:
            current_priority_level = client['priority_level']
            new_priority_level = current_priority_level - 1  # Prioritate mai mare (număr mai mic)

            # Asigură-te că noua prioritate este validă și are un tip de client asociat
            new_client_type = get_client_type_for_priority(new_priority_level)
            if new_client_type:
                # Păstrăm timpul de servire original, actualizăm doar numele clientului și prioritatea
                # Sau, dacă se dorește, se poate prelua noul timp de servire din client_priorities
                cursor.execute("UPDATE clients SET client_name = ?, priority_level = ? WHERE id = ?",
                               (new_client_type, new_priority_level, client['id']))
                updated_clients_count += 1
            else:
                print(f"Warning: No client type defined for new priority {new_priority_level}. Client ID {client['id']} not updated.")

    if updated_clients_count > 0:
        print(f"{updated_clients_count} clienți au avut prioritatea crescută datorită timpului de așteptare.")
    
    conn.commit()
    conn.close()

def main():
    init_db() # Initialize database and table
    simulated_current_time = datetime.datetime.now() # Initialize simulated time
    print(f"=== Sistem Gestionare Cozi cu Prioritate şi ETA (cu SQLite) ===")
    print(f"Timpul simulat inițial: {simulated_current_time.strftime('%Y-%m-%d %H:%M:%S')}")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM clients")
    client_count_in_db = cursor.fetchone()[0]
    conn.close()

    if client_count_in_db == 0:
        print("Baza de date este goală. Se generează 100 de clienți inițiali...")
        types_available = list(client_types.keys()) 
        weights = list(client_types.values())
        
        conn_populate = get_db_connection()
        cursor_populate = conn_populate.cursor()
        for _ in range(100):
            selected_client_type_name = random.choices(types_available, weights=weights, k=1)[0]
            prio_level, _ = client_priorities[selected_client_type_name] # Ignorăm timpul tipic din dicționar
            serving_time = random.randint(5, 30) # Generăm timp de servire random în secunde
            # Use simulated_current_time for initial population
            cursor_populate.execute("INSERT INTO clients (client_name, priority_level, serving_time, added_timestamp) VALUES (?, ?, ?, ?)",
                               (selected_client_type_name, prio_level, serving_time, simulated_current_time))
        conn_populate.commit()
        conn_populate.close()
        print(f"100 de clienți inițiali adăugați în baza de date (la timpul simulat {simulated_current_time.strftime('%Y-%m-%d %H:%M:%S')}).")

    while True:
        print(f"\\nTimpul simulat curent: {simulated_current_time.strftime('%Y-%m-%d %H:%M:%S')}") # Display current simulated time
        store_status = "🔒 ÎNCHIS" if store_closing_mode else "🟢 DESCHIS"
        auto_status = "🤖 AUTOMAT" if auto_serving_mode else "👤 MANUAL"
        heap_status = "🔺 MAX-HEAP" if max_heap_mode else "🔻 MIN-HEAP"
        print(f"Status magazin: {store_status} | Servire: {auto_status} | Mod prioritate: {heap_status}")
        afisare_coada()
        alegere = input("\\n[A] Adaugă clienți, [S] Servește următorul client, [T] Comută servire automată, [R] Pornește servirea automată, [U] Actualizează prioritatea, [D] Șterge clienți, [E] Calculează ETA client, [F] Filtrare, [C] Comută modul închidere, [H] Comută modul heap (MAX/MIN), [J] Avansează Timpul (+5m) și Ajustează Prioritățile, [I] Ieșire: ").strip().lower() # Updated menu
        
        if alegere == 'a':
            adauga_clienti_bundle(simulated_current_time) # Pass simulated_current_time
        elif alegere == 's':
            simulated_current_time = serve_next(simulated_current_time) # Actualizăm timpul simulat
        elif alegere == 't':
            toggle_auto_serving_mode()
        elif alegere == 'r':
            simulated_current_time = auto_serve_clients(simulated_current_time)
        elif alegere == 'u':
            update_priority()
        elif alegere == 'd': 
            sterge_clienti_bundle()
        elif alegere == 'e':
            calculate_eta_for_client()
        elif alegere == 'f':
            filter_menu()
        elif alegere == 'c':
            toggle_store_closing_mode()
        elif alegere == 'h':
            toggle_heap_mode()
        elif alegere == 'j': 
            simulated_current_time += datetime.timedelta(minutes=5) # Advance time by 5 minutes
            print(f"Timpul a fost avansat cu 5 minute. Noul timp simulat: {simulated_current_time.strftime('%Y-%m-%d %H:%M:%S')}")
            adaptive_priority_adjustment(simulated_current_time) # Call with new simulated time
        elif alegere == 'i':
            print("La revedere!")
            break
        else:
            print("Opțiune invalidă, vă rog încercați din nou.")

if __name__ == "__main__":
    main()
