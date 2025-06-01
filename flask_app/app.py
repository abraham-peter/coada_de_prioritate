from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
import datetime
import os
import random
import sys

# Add the parent directory to sys.path to import from main.py
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import the exact configurations from main.py
from main import client_priorities, filter_clients_by_index, filter_clients_by_priority, filter_clients_by_serving_time, toggle_heap_mode
import main  # Import the main module to access updated variables

# Store closing mode - when True, no new clients are accepted
store_closing_mode = False

# Auto serving mode - when True, clients are served automatically
# We'll store this in a file to persist across restarts
AUTO_SERVING_STATE_FILE = os.path.join(os.path.dirname(__file__), 'auto_serving_state.txt')

def get_auto_serving_mode():
    """Get the current auto-serving mode from file"""
    try:
        if os.path.exists(AUTO_SERVING_STATE_FILE):
            with open(AUTO_SERVING_STATE_FILE, 'r') as f:
                return f.read().strip().lower() == 'true'
        return False
    except:
        return False

def set_auto_serving_mode(enabled):
    """Set the auto-serving mode in file"""
    try:
        with open(AUTO_SERVING_STATE_FILE, 'w') as f:
            f.write('true' if enabled else 'false')
    except:
        pass

app = Flask(__name__)
app.secret_key = 'your_very_secret_key' # Needed for flashing messages

# Database setup (using main.py's configuration)
DB_NAME = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'queue.db')

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db_flask():
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

# Initialize the database when the app starts
init_db_flask()

def get_client_type_by_priority_level(priority_level):
    for type_name, (level, _) in client_priorities.items():
        if level == priority_level:
            return type_name
    return "unknown_type"

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor()    # Order based on heap mode: main.max_heap_mode=True means ascending (higher priority first), False means descending
    order_direction = "ASC" if main.max_heap_mode else "DESC"
    cursor.execute(f"SELECT id, client_name, priority_level, serving_time, added_timestamp FROM clients ORDER BY priority_level {order_direction}, added_timestamp")
    clients_in_db = cursor.fetchall()
    conn.close()
    queue_with_details = []
    cumulative_eta = 0
    for client_row in clients_in_db:
        # Calculate cumulative ETA - each client waits for all previous clients to finish
        cumulative_eta += client_row['serving_time']
        queue_with_details.append({
            "id": client_row['id'],
            "name": client_row['client_name'],
            "type": get_client_type_by_priority_level(client_row['priority_level']),
            "priority": client_row['priority_level'],
            "serving_time": client_row['serving_time'],
            "added_timestamp": client_row['added_timestamp'],
            "eta_start_serve": cumulative_eta  # Use cumulative ETA
        })
    
    # Calculate statistics for the dashboard
    stats = {
        'total_clients': len(queue_with_details),
        'total_eta': cumulative_eta,
        'next_client': queue_with_details[0] if queue_with_details else None,
        'avg_serving_time': cumulative_eta / len(queue_with_details) if queue_with_details else 0
    }
    
    # Get heap mode status for template
    heap_mode_status = "MAX-HEAP" if main.max_heap_mode else "MIN-HEAP"
    heap_mode_emoji = "🔺" if main.max_heap_mode else "🔻"
    
    return render_template('index.html', 
                         queue=queue_with_details, 
                         client_types_dict=client_priorities, 
                         stats=stats, 
                         store_closing_mode=store_closing_mode, 
                         auto_serving_mode=get_auto_serving_mode(),
                         heap_mode_status=heap_mode_status,
                         heap_mode_emoji=heap_mode_emoji)

@app.route('/add', methods=['POST'])
@app.route('/add_client', methods=['POST'])
def add_client():
    # Check store closing mode
    if store_closing_mode:
        flash('⚠️ Magazinul este în modul de închidere! Nu se mai acceptă clienți noi.', 'warning')
        return redirect(url_for('index'))
        
    client_type_name = request.form.get('client_type')
    num_clients = request.form.get('num_clients', type=int, default=1)

    if not client_type_name or client_type_name not in client_priorities:
        flash('Tip de client invalid.', 'error')
        return redirect(url_for('index'))
        return redirect(url_for('index'))
    if num_clients < 1:
        flash('Numărul de clienți trebuie să fie cel puțin 1.', 'error')
        return redirect(url_for('index'))

    priority_level, _ = client_priorities[client_type_name]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    for _ in range(num_clients):
        # Use random serving time like main.py does (5-30 seconds)
        serving_time = random.randint(5, 30)
        cursor.execute("INSERT INTO clients (client_name, priority_level, serving_time, added_timestamp) VALUES (?, ?, ?, ?)",
                       (client_type_name, priority_level, serving_time, datetime.datetime.now()))
    conn.commit()
    conn.close()
    flash(f'{num_clients} client(i) de tip "{client_type_name}" adăugat(i) cu succes.', 'success')
    return redirect(url_for('index'))

@app.route('/serve_next_client', methods=['POST'])
def serve_next_client():
    print("DEBUG: serve_next_client function called!")  # Debug line
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Order based on heap mode for serving next client
    order_direction = "ASC" if main.max_heap_mode else "DESC"
    cursor.execute(f"SELECT id, client_name, priority_level, serving_time FROM clients ORDER BY priority_level {order_direction}, added_timestamp LIMIT 1")
    client_to_serve = cursor.fetchone()

    if client_to_serve:
        print(f"DEBUG: Serving client: {client_to_serve['client_name']}")  # Debug line
        cursor.execute("DELETE FROM clients WHERE id = ?", (client_to_serve['id'],))
        
        # Add a new random client after serving one (like main.py does)
        types_available = list(client_priorities.keys()) 
        weights = [1] * len(types_available)  # Equal weights for all client types
        selected_client_type_name = random.choices(types_available, weights=weights, k=1)[0]
        prio_level, _ = client_priorities[selected_client_type_name]
        serving_time = random.randint(5, 30)
        
        cursor.execute("INSERT INTO clients (client_name, priority_level, serving_time, added_timestamp) VALUES (?, ?, ?, ?)",
                       (selected_client_type_name, prio_level, serving_time, datetime.datetime.now()))
        
        conn.commit()
        flash(f"Clientul '{client_to_serve['client_name']}' (Prioritate {client_to_serve['priority_level']}) a fost servit. Un client nou '{selected_client_type_name}' a fost adăugat.", 'success')
    else:
        print("DEBUG: No clients to serve")  # Debug line
        flash("Coada este goală. Nu există clienți de servit.", 'info')
    
    conn.close()
    print("DEBUG: Redirecting to index")  # Debug line
    return redirect(url_for('index'))

@app.route('/delete_by_priority', methods=['POST'])
def delete_by_priority_route():
    try:
        priority_to_delete = int(request.form.get('priority_level_delete'))
    except (ValueError, TypeError):
        flash("Prioritate invalidă pentru ștergere.", "error")
        return redirect(url_for('index'))

    if not 1 <= priority_to_delete <= len(client_priorities): # Max priority level
         flash(f"Prioritatea pentru ștergere trebuie să fie între 1 și {len(client_priorities)}.", "error")
         return redirect(url_for('index'))

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # First, count how many clients match this priority to decide how many to delete
    cursor.execute("SELECT id FROM clients WHERE priority_level = ? ORDER BY added_timestamp", (priority_to_delete,))
    clients_found = cursor.fetchall()
    num_found = len(clients_found)

    if num_found == 0:
        flash(f"Nu există clienți cu prioritatea {priority_to_delete}.", 'info')
        conn.close()
        return redirect(url_for('index'))

    try:
        count_to_delete = int(request.form.get('num_to_delete', 1))
    except (ValueError, TypeError):
        flash("Număr invalid de clienți pentru șters.", "error")
        conn.close()
        return redirect(url_for('index'))
        
    if count_to_delete < 1:
        flash("Numărul de clienți pentru șters trebuie să fie cel puțin 1.", "error")
        conn.close()
        return redirect(url_for('index'))
    
    count_to_delete = min(count_to_delete, num_found) # Don't try to delete more than exist

    clients_to_delete_ids = [client['id'] for client in clients_found[:count_to_delete]]

    for client_id in clients_to_delete_ids:
        cursor.execute("DELETE FROM clients WHERE id = ?", (client_id,))
    
    conn.commit()
    conn.close()
    flash(f"{count_to_delete} client(i) cu prioritatea {priority_to_delete} au fost șterși.", 'success')
    return redirect(url_for('index'))

@app.route('/delete_clients', methods=['POST'])
def delete_clients():
    """Delete clients by priority level - alternative route name for template compatibility"""
    try:
        priority_level = int(request.form.get('priority_level'))
        count = int(request.form.get('count', 1))
    except (ValueError, TypeError):
        flash("Prioritate sau număr invalid.", "error")
        return redirect(url_for('index'))

    if not 1 <= priority_level <= 8:
        flash("Prioritatea trebuie să fie între 1 și 8.", "error")
        return redirect(url_for('index'))

    if count < 1:
        flash("Numărul de clienți trebuie să fie cel puțin 1.", "error")
        return redirect(url_for('index'))

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get clients with the specified priority
    cursor.execute("SELECT id FROM clients WHERE priority_level = ? ORDER BY added_timestamp LIMIT ?", 
                  (priority_level, count))
    clients_to_delete = cursor.fetchall()
    
    if not clients_to_delete:
        flash(f"Nu există clienți cu prioritatea {priority_level}.", 'info')
        conn.close()
        return redirect(url_for('index'))
    
    # Delete the clients
    for client in clients_to_delete:
        cursor.execute("DELETE FROM clients WHERE id = ?", (client['id'],))
    
    conn.commit()
    conn.close()
    
    deleted_count = len(clients_to_delete)
    flash(f"{deleted_count} client(i) cu prioritatea {priority_level} au fost șterși.", 'success')
    return redirect(url_for('index'))

@app.route('/clear_queue', methods=['POST'])
def clear_queue():
    """Clear all clients from the queue"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Count current clients
    cursor.execute("SELECT COUNT(*) as count FROM clients")
    count_result = cursor.fetchone()
    total_clients = count_result['count'] if count_result else 0
    
    # Clear all clients
    cursor.execute("DELETE FROM clients")
    conn.commit()
    conn.close()
    
    if total_clients > 0:
        flash(f"Toate cele {total_clients} persoane din coadă au fost șterse.", 'success')
    else:
        flash("Coada era deja goală.", 'info')
    
    return redirect(url_for('index'))

@app.route('/update_priority', methods=['POST'])
def update_priority_route():
    try:
        client_id_to_update = int(request.form.get('client_id_update'))
        new_priority_type_name = request.form.get('new_priority_type_update')
    except (ValueError, TypeError):
        flash("ID client sau tip prioritate invalid.", "error")
        return redirect(url_for('index'))

    if not new_priority_type_name or new_priority_type_name not in client_priorities:
        flash('Noul tip de prioritate este invalid.', 'error')
        return redirect(url_for('index'))

    new_priority_level, new_serving_time = client_priorities[new_priority_type_name]

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Fetch the client to confirm it exists
    cursor.execute("SELECT id, client_name, serving_time FROM clients WHERE id = ?", (client_id_to_update,))
    client = cursor.fetchone()

    if not client:
        flash(f"Clientul cu ID {client_id_to_update} nu a fost găsit.", 'error')
        conn.close()
        return redirect(url_for('index'))

    # As per main.py logic: client_name changes to new type, priority_level changes,
    # BUT original serving_time was preserved.
    # For the web version, let's decide:
    # Option A: Preserve original serving time (as in latest main.py)
    # Option B: Update serving time to that of the new priority type (simpler for web UI if not specified)
    # Let's go with Option B for now as it's more aligned with changing client "type".
    # If original serving time must be kept, we'd use client['serving_time'] instead of new_serving_time.
    
    # For Option B (serving time changes with new priority type):
    # cursor.execute("UPDATE clients SET client_name = ?, priority_level = ?, serving_time = ? WHERE id = ?",
    #                (new_priority_type_name, new_priority_level, serving_time, client_id_to_update))

    # For Option A (preserve original serving time, change name and priority):
    # This matches the console app's "update_priority" behavior more closely.
    original_serving_time = client['serving_time']
    cursor.execute("UPDATE clients SET client_name = ?, priority_level = ?, serving_time = ? WHERE id = ?",
                   (new_priority_type_name, new_priority_level, original_serving_time, client_id_to_update))


    conn.commit()
    conn.close()
    flash(f"Prioritatea clientului ID {client_id_to_update} (nume vechi: {client['client_name']}) a fost actualizată la '{new_priority_type_name}' (Nivel {new_priority_level}). Timpul de servire a rămas {original_serving_time}s.", 'success')
    return redirect(url_for('index'))


@app.route('/calculate_eta_for_client', methods=['POST'])
def calculate_eta_route_specific():
    try:
        client_id_for_eta = int(request.form.get('client_id_for_eta'))
    except (ValueError, TypeError):
        flash("ID client invalid pentru calcul ETA.", "error")
        return redirect(url_for('index'))

    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Order based on heap mode for ETA calculation
    order_direction = "ASC" if main.max_heap_mode else "DESC"
    cursor.execute(f"SELECT id, client_name, priority_level, serving_time FROM clients ORDER BY priority_level {order_direction}, added_timestamp")
    all_clients_ordered = cursor.fetchall()
    conn.close()

    eta_info = None
    if not all_clients_ordered:
        flash("Coada este goală. Nu se poate calcula ETA.", 'info')
    else:
        cumulative_time_before = 0
        found_client = None
        for client_row in all_clients_ordered:
            if client_row['id'] == client_id_for_eta:
                found_client = client_row
                break
            cumulative_time_before += client_row['serving_time']
        
        if found_client:
            eta_info = {
                "name": found_client['client_name'],
                "priority": found_client['priority_level'],
                "wait_time": cumulative_time_before,
                "serving_time": found_client['serving_time'],
                "finish_eta": cumulative_time_before + found_client['serving_time']
            }
            flash(f"ETA pentru clientul '{eta_info['name']}': Așteptare: {eta_info['wait_time']}s, Servire: {eta_info['serving_time']}s, Finalizare în: {eta_info['finish_eta']}s.", "success")
        else:
            flash(f"Clientul cu ID {client_id_for_eta} nu a fost găsit în coadă.", "warning")
            
    # Re-fetch queue for display as flash messages don't pass complex objects easily to template context directly
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Order based on heap mode for redisplay    order_direction = "ASC" if main.max_heap_mode else "DESC"
    cursor.execute(f"SELECT id, client_name, priority_level, serving_time, added_timestamp FROM clients ORDER BY priority_level {order_direction}, added_timestamp")
    clients_in_db_redisplay = cursor.fetchall()
    conn.close()
    queue_with_details_redisplay = []
    cumulative_eta_redisplay = 0
    for client_row_redisplay in clients_in_db_redisplay:
        # Calculate cumulative ETA for redisplay
        cumulative_eta_redisplay += client_row_redisplay['serving_time']
        queue_with_details_redisplay.append({
            "id": client_row_redisplay['id'],
            "name": client_row_redisplay['client_name'],
            "type": get_client_type_by_priority_level(client_row_redisplay['priority_level']),
            "priority": client_row_redisplay['priority_level'],
            "serving_time": client_row_redisplay['serving_time'],
            "added_timestamp": client_row_redisplay['added_timestamp'],
            "eta_start_serve": cumulative_eta_redisplay  # Use cumulative ETA
        })

    # Get heap mode status for template
    heap_mode_status = "MAX-HEAP" if main.max_heap_mode else "MIN-HEAP"
    heap_mode_emoji = "🔺" if main.max_heap_mode else "🔻"
    
    return render_template('index.html', 
                         queue=queue_with_details_redisplay, 
                         client_types_dict=client_priorities, 
                         total_eta=cumulative_eta_redisplay, 
                         calculated_eta_specific=eta_info, 
                         store_closing_mode=store_closing_mode, 
                         auto_serving_mode=get_auto_serving_mode(),
                         heap_mode_status=heap_mode_status,
                         heap_mode_emoji=heap_mode_emoji)

@app.route('/advance_time', methods=['POST'])
def advance_time():
    """Advance simulated time and adjust priorities like main.py's 'J' option"""
    try:
        # Import the adaptive priority adjustment function
        from main import adaptive_priority_adjustment
        
        # Simulate advancing time by 5 minutes
        simulated_current_time = datetime.datetime.now() + datetime.timedelta(minutes=5)
        adaptive_priority_adjustment(simulated_current_time)
        
        flash(f"Timpul a fost avansat cu 5 minute și prioritățile au fost ajustate automat.", 'success')
    except Exception as e:
        flash(f"Eroare la avansarea timpului: {str(e)}", 'error')
    
    return redirect(url_for('index'))

@app.route('/toggle_store_mode', methods=['POST'])
def toggle_store_mode():
    global store_closing_mode
    store_closing_mode = not store_closing_mode
    status = "ACTIVAT" if store_closing_mode else "DEZACTIVAT"
    message = "⚠️ Nu se mai acceptă clienți noi!" if store_closing_mode else "✅ Se acceptă clienți noi."
    flash(f"Modul închidere magazin: {status}. {message}", 'info')
    return redirect(url_for('index'))

@app.route('/auto_serve_status', methods=['GET'])
def auto_serve_status():
    """Return the current auto-serving status for AJAX calls"""
    return jsonify({'auto_serving': get_auto_serving_mode()})

@app.route('/next_client_info', methods=['GET'])
def next_client_info():
    """Return information about the next client to be served"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Order based on heap mode
    order_direction = "ASC" if main.max_heap_mode else "DESC"
    cursor.execute(f"SELECT id, client_name, priority_level, serving_time FROM clients ORDER BY priority_level {order_direction}, added_timestamp LIMIT 1")
    next_client = cursor.fetchone()
    conn.close()
    
    if next_client:
        return jsonify({
            'has_client': True,
            'client_id': next_client['id'],
            'client_name': next_client['client_name'],
            'priority_level': next_client['priority_level'],
            'serving_time': next_client['serving_time']
        })
    else:
        return jsonify({
            'has_client': False
        })

@app.route('/toggle_auto_serving', methods=['POST'])
def toggle_auto_serving():
    current_mode = get_auto_serving_mode()
    new_mode = not current_mode
    set_auto_serving_mode(new_mode)
    status = "ACTIVAT" if new_mode else "DEZACTIVAT"
    message = "🤖 Servirea automată a fost pornită!" if new_mode else "⏹️ Servirea automată a fost oprită."
    flash(f"Servire automată: {status}. {message}", 'info')
    return redirect(url_for('index'))

@app.route('/toggle_heap_mode', methods=['POST'])
def toggle_heap_mode_route():
    """Toggle between max-heap and min-heap serving modes"""
    current_mode = toggle_heap_mode()  # This calls the main.py function which toggles and returns new mode
    mode_name = "MAX-HEAP" if current_mode else "MIN-HEAP"
    emoji = "🔺" if current_mode else "🔻"
    message = f"Modul de servire schimbat la: {mode_name}"
    flash(f"{emoji} {message}", 'info')
    return redirect(url_for('index'))

@app.route('/filter', methods=['GET', 'POST'])
def filter_clients():
    if request.method == 'POST':
        filter_type = request.form.get('filter_type')
        
        if filter_type == 'index':
            start_index = request.form.get('start_index')
            end_index = request.form.get('end_index')
            
            start_idx = int(start_index) if start_index else None
            end_idx = int(end_index) if end_index else None
            
            filtered_clients = filter_clients_by_index(start_idx, end_idx)
            filter_desc = f"Index {start_idx or 1} - {end_idx or 'sfârșit'}"
            
        elif filter_type == 'priority':
            priority_input = request.form.get('priorities')
            if priority_input:
                priority_levels = [int(p.strip()) for p in priority_input.split(',')]
                # Validate priorities
                invalid_prios = [p for p in priority_levels if p < 1 or p > 8]
                if invalid_prios:
                    flash(f"Priorități invalide: {invalid_prios}. Folosiți valori între 1-8.", 'error')
                    return redirect(url_for('filter_clients'))
            else:
                priority_levels = None
            
            filtered_clients = filter_clients_by_priority(priority_levels)
            filter_desc = f"Priorități: {','.join(map(str, priority_levels))}" if priority_levels else "Toate prioritățile"
            
        elif filter_type == 'serving_time':
            min_time = request.form.get('min_time')
            max_time = request.form.get('max_time')
            
            min_t = int(min_time) if min_time else None
            max_t = int(max_time) if max_time else None
            
            if min_t is not None and min_t < 0:
                flash("Timpul minim nu poate fi negativ.", 'error')
                return redirect(url_for('filter_clients'))
            if max_t is not None and max_t < 0:
                flash("Timpul maxim nu poate fi negativ.", 'error')
                return redirect(url_for('filter_clients'))
            if min_t is not None and max_t is not None and min_t > max_t:
                flash("Timpul minim nu poate fi mai mare decât timpul maxim.", 'error')
                return redirect(url_for('filter_clients'))
            
            filtered_clients = filter_clients_by_serving_time(min_t, max_t)
            filter_desc = f"Timp servire: {min_t or 0}s - {max_t or '∞'}s"
        
        else:
            flash("Tip de filtrare invalid.", 'error')
            return redirect(url_for('filter_clients'))        # Calculate ETA for filtered clients
        filtered_with_eta = []
        cumulative_eta = 0
        for client in filtered_clients:
            cumulative_eta += client['serving_time']
            client_info = {
                'id': client['id'],
                'client_name': client['client_name'],
                'priority_level': client['priority_level'],
                'serving_time': client['serving_time'],
                'added_timestamp': client['added_timestamp'],
                'eta_start': cumulative_eta  # Use cumulative ETA
            }
            filtered_with_eta.append(client_info)
        
        total_eta = cumulative_eta
        
        # Get all clients for the main view
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Order based on heap mode for filter results
        order_direction = "ASC" if main.max_heap_mode else "DESC"
        cursor.execute(f"SELECT client_name, priority_level, serving_time, added_timestamp FROM clients ORDER BY priority_level {order_direction}, added_timestamp")
        all_clients_in_db = cursor.fetchall()
        conn.close()        # Build queue details for main view
        queue_with_details = []
        cumulative_eta_all = 0
        for client_row in all_clients_in_db:
            # Calculate cumulative ETA
            cumulative_eta_all += client_row['serving_time']
            queue_with_details.append({
                "id": client_row['id'] if 'id' in client_row.keys() else 0,
                "name": client_row['client_name'],
                "type": get_client_type_by_priority_level(client_row['priority_level']),
                "priority": client_row['priority_level'],
                "serving_time": client_row['serving_time'],
                "added_timestamp": client_row['added_timestamp'],
                "eta_start_serve": cumulative_eta_all  # Use cumulative ETA
            })

        # Calculate statistics for the dashboard
        stats = {
            'total_clients': len(queue_with_details),
            'total_eta': cumulative_eta_all,
            'next_client': queue_with_details[0] if queue_with_details else None,
            'avg_serving_time': cumulative_eta_all / len(queue_with_details) if queue_with_details else 0        }
        
        flash(f"Filtru aplicat: {filter_desc}. Găsiți {len(filtered_with_eta)} clienți cu timpul total de {total_eta}s.", 'info')
        
        # Get heap mode status for template
        heap_mode_status = "MAX-HEAP" if main.max_heap_mode else "MIN-HEAP"
        heap_mode_emoji = "🔺" if main.max_heap_mode else "🔻"
        
        return render_template('index.html', 
                             queue=queue_with_details, 
                             client_types_dict=client_priorities, 
                             stats=stats,
                             store_closing_mode=store_closing_mode,
                             auto_serving_mode=get_auto_serving_mode(),
                             filtered_clients=filtered_with_eta,
                             filter_description=filter_desc,
                             show_filtered=True,
                             heap_mode_status=heap_mode_status,
                             heap_mode_emoji=heap_mode_emoji)
    
    # If GET request, show the main page
    conn = get_db_connection()
    cursor = conn.cursor()
      # Order based on heap mode for GET request
    order_direction = "ASC" if main.max_heap_mode else "DESC"
    cursor.execute(f"SELECT client_name, priority_level, serving_time, added_timestamp FROM clients ORDER BY priority_level {order_direction}, added_timestamp")
    clients_in_db = cursor.fetchall()
    conn.close()
    queue_with_details = []
    cumulative_eta = 0
    for client_row in clients_in_db:
        # Calculate cumulative ETA
        cumulative_eta += client_row['serving_time']
        queue_with_details.append({
            "id": client_row['id'] if 'id' in client_row.keys() else 0,
            "name": client_row['client_name'],
            "type": get_client_type_by_priority_level(client_row['priority_level']),
            "priority": client_row['priority_level'],
            "serving_time": client_row['serving_time'],
            "added_timestamp": client_row['added_timestamp'],
            "eta_start_serve": cumulative_eta  # Use cumulative ETA
        })

    stats = {
        'total_clients': len(queue_with_details),
        'total_eta': cumulative_eta,
        'next_client': queue_with_details[0] if queue_with_details else None,
        'avg_serving_time': cumulative_eta / len(queue_with_details) if queue_with_details else 0
    }
    
    # Get heap mode status for template
    heap_mode_status = "MAX-HEAP" if main.max_heap_mode else "MIN-HEAP"
    heap_mode_emoji = "🔺" if main.max_heap_mode else "🔻"
    
    return render_template('index.html', 
                         queue=queue_with_details, 
                         client_types_dict=client_priorities, 
                         stats=stats,
                         store_closing_mode=store_closing_mode,
                         auto_serving_mode=get_auto_serving_mode(),
                         heap_mode_status=heap_mode_status,
                         heap_mode_emoji=heap_mode_emoji)


if __name__ == '__main__':
    # Ensure the database file is in the parent directory of flask_app
    # The DB_NAME is constructed to point there.
    # Example: if app.py is in C:/.../cozi_de_prioritate/flask_app/app.py
    # DB_NAME will be C:/.../cozi_de_prioritate/queue.db
    print(f"Database will be accessed at: {DB_NAME}")
    if not os.path.exists(os.path.dirname(DB_NAME)) and os.path.dirname(DB_NAME) != '':
         os.makedirs(os.path.dirname(DB_NAME)) # Create parent directory if it doesn't exist
    
    init_db_flask() # Make sure table exists
    app.run(debug=True, port=5001) # Using port 5001 to avoid common conflicts
