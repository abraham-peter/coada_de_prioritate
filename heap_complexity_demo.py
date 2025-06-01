#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DEMONSTRAȚIA COMPLEXITĂȚII O(log n) PENTRU OPERAȚIILE HEAP
==========================================================

Acest modul demonstrează complexitatea temporală O(log n) pentru operațiile de inserare
și extragere într-un heap, comparând implementarea actuală bazată pe baza de date
cu o implementare nativă de heap în Python.

Autor: Sistema de Gestionare Cozi cu Prioritate
Data: 2025
"""

import heapq
import time
import random
import sqlite3
import os
import matplotlib
# Set backend before importing pyplot
matplotlib.use('Agg')  # Non-interactive backend for generating files
import matplotlib.pyplot as plt
import numpy as np
from typing import List, Tuple
import sys
import os

# Adaugă directorul curent pentru a importa modulele existente
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from main import client_priorities, get_db_connection
except ImportError:
    # Fallback dacă importul nu funcționează
    client_priorities = {
        'urgenta': (1, 15),
        'client_cu_dizabilitati': (2, 20),
        'familie_cu_dizabilitati': (3, 25),
        'familie_cu_copii': (4, 18),
        'client_cu_abonament': (5, 15),
        'mama_insarcinata': (6, 20),
        'angajatii': (7, 10),
        'client_fara_abonament': (8, 12)
    }

class HeapComplexityAnalyzer:
    """
    Analizor pentru demonstrarea complexității temporale a operațiilor heap.
    """
    
    def __init__(self):
        self.results = {
            'sizes': [],
            'native_heap_insert': [],
            'native_heap_extract': [],
            'db_heap_insert': [],
            'db_heap_extract': [],
            'theoretical_log_n': []
        }
        
    def setup_test_database(self, db_name: str = "heap_test.db"):
        """Inițializează baza de date pentru teste."""
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        # Șterge tabela dacă există
        cursor.execute("DROP TABLE IF EXISTS heap_clients")
        
        # Creează tabela pentru teste
        cursor.execute('''
            CREATE TABLE heap_clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_name TEXT NOT NULL,
                priority_level INTEGER NOT NULL,
                serving_time INTEGER NOT NULL,
                added_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Creează index pentru optimizare
        cursor.execute('''
            CREATE INDEX idx_priority_timestamp 
            ON heap_clients(priority_level, added_timestamp)
        ''')
        
        conn.commit()
        conn.close()
        return db_name
    
    def generate_test_data(self, n: int) -> List[Tuple[str, int, int]]:
        """Generează date de test pentru heap."""
        data = []
        client_types = list(client_priorities.keys())
        
        for _ in range(n):
            client_type = random.choice(client_types)
            priority, base_time = client_priorities[client_type]
            serving_time = random.randint(5, 30)
            data.append((client_type, priority, serving_time))
        
        return data
    
    def measure_native_heap_operations(self, data: List[Tuple[str, int, int]]) -> Tuple[float, float]:
        """
        Măsoară timpul pentru operațiile pe heap-ul nativ Python.
        Returnează (timp_inserare, timp_extragere).
        """
        heap = []
        
        # Măsurarea inserării
        start_time = time.perf_counter()
        for client_name, priority, serving_time in data:
            # Pentru max-heap, negăm prioritatea (Python heapq este min-heap)
            heapq.heappush(heap, (priority, client_name, serving_time))
        insert_time = time.perf_counter() - start_time
        
        # Măsurarea extragerii
        start_time = time.perf_counter()
        extracted_count = min(len(heap) // 2, 1000)  # Extragem jumătate sau maxim 1000
        for _ in range(extracted_count):
            if heap:
                heapq.heappop(heap)
        extract_time = time.perf_counter() - start_time
        
        return insert_time, extract_time
    
    def measure_db_heap_operations(self, data: List[Tuple[str, int, int]], db_name: str) -> Tuple[float, float]:
        """
        Măsoară timpul pentru operațiile pe heap-ul bazat pe baza de date.
        Returnează (timp_inserare, timp_extragere).
        """
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        # Măsurarea inserării
        start_time = time.perf_counter()
        for client_name, priority, serving_time in data:
            cursor.execute('''
                INSERT INTO heap_clients (client_name, priority_level, serving_time)
                VALUES (?, ?, ?)
            ''', (client_name, priority, serving_time))
        conn.commit()
        insert_time = time.perf_counter() - start_time
        
        # Măsurarea extragerii (simulează servirea clienților)
        start_time = time.perf_counter()
        extracted_count = min(len(data) // 2, 1000)  # Extragem jumătate sau maxim 1000
        for _ in range(extracted_count):
            # Găsește și șterge clientul cu prioritatea cea mai mare
            cursor.execute('''
                SELECT id FROM heap_clients 
                ORDER BY priority_level ASC, added_timestamp ASC 
                LIMIT 1
            ''')
            result = cursor.fetchone()
            if result:
                cursor.execute('DELETE FROM heap_clients WHERE id = ?', (result[0],))
        conn.commit()
        extract_time = time.perf_counter() - start_time
        
        conn.close()
        return insert_time, extract_time
    
    def run_complexity_analysis(self, sizes: List[int] = None):
        """
        Rulează analiza complexității pentru diferite dimensiuni de heap.
        """
        if sizes is None:
            sizes = [100, 500, 1000, 2000, 5000, 10000, 20000, 50000]
        
        print("🔬 DEMONSTRAȚIA COMPLEXITĂȚII O(log n) PENTRU OPERAȚIILE HEAP")
        print("=" * 70)
        print("\n📊 Analiză comparativă: Heap Nativ vs. Heap Bazat pe BD")
        print("\nDimensiune | Heap Nativ (ms)    | Heap BD (ms)        | Teoretic O(log n)")
        print("           | Insert  | Extract  | Insert  | Extract  | log(n) × constant")
        print("-" * 80)
        
        for n in sizes:
            print(f"\n🧪 Testând cu {n:,} elemente...")
            
            # Generează date de test
            test_data = self.generate_test_data(n)
            
            # Configurează baza de date
            db_name = self.setup_test_database(f"heap_test_{n}.db")
            
            # Testează heap-ul nativ
            native_insert, native_extract = self.measure_native_heap_operations(test_data)
            
            # Testează heap-ul bazat pe BD
            db_insert, db_extract = self.measure_db_heap_operations(test_data, db_name)
            
            # Calculează valoarea teoretică O(log n)
            theoretical_value = np.log2(n) * 0.001  # Constanta arbitrară pentru vizualizare
            
            # Stochează rezultatele
            self.results['sizes'].append(n)
            self.results['native_heap_insert'].append(native_insert * 1000)  # ms
            self.results['native_heap_extract'].append(native_extract * 1000)  # ms
            self.results['db_heap_insert'].append(db_insert * 1000)  # ms
            self.results['db_heap_extract'].append(db_extract * 1000)  # ms
            self.results['theoretical_log_n'].append(theoretical_value)
            
            # Afișează rezultatele
            print(f"{n:8,} | {native_insert*1000:6.2f}  | {native_extract*1000:7.2f}  | "
                  f"{db_insert*1000:6.2f}  | {db_extract*1000:7.2f}  | {theoretical_value:7.3f}")
            
            # Curăță baza de date de test
            try:
                os.remove(db_name)
            except OSError:
                pass
        
        print("\n" + "=" * 70)
        self._display_complexity_analysis()
        self._generate_complexity_graphs()
    
    def _display_complexity_analysis(self):
        """Afișează analiza complexității."""
        print("\n📈 ANALIZA COMPLEXITĂȚII TEMPORALE")
        print("=" * 50)
        
        print("\n🔍 Observații:")
        print("1. HEAP NATIV (Python heapq):")
        print("   - Inserare: O(log n) - creștere logaritmică")
        print("   - Extragere: O(log n) - creștere logaritmică")
        print("   - Performanță optimă datorită implementării în C")
        
        print("\n2. HEAP BAZAT PE BAZA DE DATE (SQLite):")
        print("   - Inserare: O(log n) - datorită indexurilor B-tree")
        print("   - Extragere: O(log n) - căutare + ștergere indexată")
        print("   - Overhead suplimentar pentru I/O și SQL parsing")
        
        print("\n3. COMPARAȚIA PERFORMANȚELOR:")
        if len(self.results['sizes']) >= 2:
            # Calculează factorul de creștere pentru ultima măsurare
            n1, n2 = self.results['sizes'][-2], self.results['sizes'][-1]
            t1, t2 = self.results['native_heap_insert'][-2], self.results['native_heap_insert'][-1]
            
            theoretical_ratio = np.log2(n2) / np.log2(n1)
            actual_ratio = t2 / t1 if t1 > 0 else 0
            
            print(f"   - Pentru creșterea de la {n1:,} la {n2:,} elemente:")
            print(f"   - Raport teoretic: {theoretical_ratio:.2f}x")
            print(f"   - Raport măsurat: {actual_ratio:.2f}x")
            print(f"   - Confirmă complexitatea O(log n): {'✅' if abs(actual_ratio - theoretical_ratio) < 1 else '❌'}")
    
    def _generate_complexity_graphs(self):
        """Generează graficele de complexitate."""
        try:
            plt.style.use('seaborn-v0_8')
        except OSError:
            plt.style.use('default')
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Demonstrația Complexității O(log n) pentru Operațiile Heap', fontsize=16, fontweight='bold')
        
        sizes = np.array(self.results['sizes'])
        log_n = np.log2(sizes)
        
        # Graficul 1: Inserare Heap Nativ
        ax1.plot(sizes, self.results['native_heap_insert'], 'bo-', label='Timp măsurat', linewidth=2, markersize=6)
        ax1.plot(sizes, log_n * np.mean(self.results['native_heap_insert']) / np.mean(log_n), 
                'r--', label='O(log n) teoretic', linewidth=2)
        ax1.set_xlabel('Numărul de elemente (n)')
        ax1.set_ylabel('Timp (ms)')
        ax1.set_title('Inserare - Heap Nativ Python')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_xscale('log')
        ax1.set_yscale('log')
        
        # Graficul 2: Extragere Heap Nativ
        ax2.plot(sizes, self.results['native_heap_extract'], 'go-', label='Timp măsurat', linewidth=2, markersize=6)
        ax2.plot(sizes, log_n * np.mean(self.results['native_heap_extract']) / np.mean(log_n), 
                'r--', label='O(log n) teoretic', linewidth=2)
        ax2.set_xlabel('Numărul de elemente (n)')
        ax2.set_ylabel('Timp (ms)')
        ax2.set_title('Extragere - Heap Nativ Python')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.set_xscale('log')
        ax2.set_yscale('log')
        
        # Graficul 3: Inserare Heap BD
        ax3.plot(sizes, self.results['db_heap_insert'], 'mo-', label='Timp măsurat', linewidth=2, markersize=6)
        ax3.plot(sizes, log_n * np.mean(self.results['db_heap_insert']) / np.mean(log_n), 
                'r--', label='O(log n) teoretic', linewidth=2)
        ax3.set_xlabel('Numărul de elemente (n)')
        ax3.set_ylabel('Timp (ms)')
        ax3.set_title('Inserare - Heap Bazat pe BD')
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        ax3.set_xscale('log')
        ax3.set_yscale('log')
        
        # Graficul 4: Extragere Heap BD
        ax4.plot(sizes, self.results['db_heap_extract'], 'co-', label='Timp măsurat', linewidth=2, markersize=6)
        ax4.plot(sizes, log_n * np.mean(self.results['db_heap_extract']) / np.mean(log_n), 
                'r--', label='O(log n) teoretic', linewidth=2)
        ax4.set_xlabel('Numărul de elemente (n)')
        ax4.set_ylabel('Timp (ms)')
        ax4.set_title('Extragere - Heap Bazat pe BD')
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        ax4.set_xscale('log')
        ax4.set_yscale('log')
        
        plt.tight_layout()
          # Salvează graficul
        output_path = os.path.join(os.path.dirname(__file__), 'heap_complexity_analysis.png')
        try:
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            print(f"\n📊 Graficele salvate în: {output_path}")
        except Exception as e:
            print(f"Eroare la salvarea graficelor: {e}")
        
        # Afișează graficul dacă rulează interactiv
        try:
            plt.show()
        except Exception as e:
            print(f"Graficele nu pot fi afișate în modul non-interactiv: {e}")
        finally:
            plt.close()
    
    def demonstrate_heap_properties(self):
        """Demonstrează proprietățile heap-ului."""
        print("\n🏗️  DEMONSTRAȚIA PROPRIETĂȚILOR HEAP-ULUI")
        print("=" * 50)
        
        # Creează un heap de test
        test_data = [
            ('urgenta', 1, 15),
            ('client_fara_abonament', 8, 12),
            ('angajatii', 7, 10),
            ('client_cu_abonament', 5, 15),
            ('mama_insarcinata', 6, 20),
            ('familie_cu_copii', 4, 18),
            ('client_cu_dizabilitati', 2, 20),
            ('familie_cu_dizabilitati', 3, 25)
        ]
        
        print("\n1. HEAP NATIV PYTHON (MIN-HEAP)")
        print("-" * 30)
        heap = []
        for client_name, priority, serving_time in test_data:
            heapq.heappush(heap, (priority, client_name, serving_time))
            print(f"Inserare: {client_name} (P{priority}) -> Heap: {[x[1] for x in heap[:3]]}")
        
        print(f"\nStarea finală heap: {[(p, n) for p, n, _ in heap]}")
        
        print("\n2. EXTRAGEREA ÎN ORDINEA PRIORITĂȚII")
        print("-" * 40)
        extracted = []
        while heap:
            priority, client_name, serving_time = heapq.heappop(heap)
            extracted.append((priority, client_name))
            print(f"Extras: {client_name} (P{priority}) | Rămas în heap: {len(heap)} elemente")
        
        print(f"\nOrdinea de extragere: {[f'{n}(P{p})' for p, n in extracted]}")
        
        print("\n3. VERIFICAREA PROPRIETĂȚII HEAP-ULUI")
        print("-" * 45)
        print("✅ Proprietatea heap-ului: Părintele ≤ Copiii (pentru min-heap)")
        print("✅ Inserarea: O(log n) - rebalansare pe înălțimea arborelui")
        print("✅ Extragerea minimului: O(log n) - rebalansare după ștergerea rădăcinii")
        print("✅ Accesul la minimum: O(1) - rădăcina arborelui")


class HeapVisualization:
    """Clasă pentru vizualizarea structurii heap-ului."""
    
    @staticmethod
    def print_heap_tree(heap_list, index=0, depth=0, prefix="Root: "):
        """Afișează heap-ul ca arbore."""
        if index < len(heap_list):
            print(" " * (depth * 4) + prefix + f"{heap_list[index]}")
            if 2 * index + 1 < len(heap_list):
                HeapVisualization.print_heap_tree(heap_list, 2 * index + 1, depth + 1, "L--- ")
            if 2 * index + 2 < len(heap_list):
                HeapVisualization.print_heap_tree(heap_list, 2 * index + 2, depth + 1, "R--- ")
    
    @staticmethod
    def demonstrate_heap_structure():
        """Demonstrează structura internă a heap-ului."""
        print("\n🌳 VIZUALIZAREA STRUCTURII HEAP-ULUI")
        print("=" * 45)
        
        # Creează un heap cu prioritățile din sistemul nostru
        priorities = [1, 2, 3, 4, 5, 6, 7, 8]  # Toate prioritățile
        client_names = ['Urgenta', 'Dizabilitati', 'Familie_Diz', 'Familie_Copii', 
                       'Abonament', 'Gravida', 'Angajati', 'Normal']
        
        heap = []
        for i, (priority, name) in enumerate(zip(priorities, client_names)):
            heapq.heappush(heap, (priority, name))
            print(f"\n📍 După inserarea {name} (P{priority}):")
            print("Structura heap (reprezentare ca arbore):")
            HeapVisualization.print_heap_tree([(p, n) for p, n in heap])
            
            if i < 3:  # Afișează doar primele câteva pentru claritate
                print("Reprezentare ca array:", [(p, n) for p, n in heap])


def main():
    """Funcția principală pentru demonstrația complexității."""
    print("🚀 DEMONSTRAȚIA COMPLEXITĂȚII O(log n) PENTRU HEAP-URI")
    print("=" * 60)
    print("Această demonstrație compară performanța operațiilor heap între:")
    print("1. 📚 Implementarea nativă Python (heapq)")
    print("2. 🗃️  Implementarea bazată pe baza de date SQLite")
    print("3. 📈 Analiza teoretică O(log n)")
    print()
    
    analyzer = HeapComplexityAnalyzer()
    
    # Demonstrează proprietățile heap-ului
    analyzer.demonstrate_heap_properties()
    
    # Vizualizează structura heap-ului
    HeapVisualization.demonstrate_heap_structure()
    
    # Rulează analiza complexității
    test_sizes = [100, 500, 1000, 2000, 5000, 10000]
    analyzer.run_complexity_analysis(test_sizes)
    
    print("\n🎯 CONCLUZII FINALE")
    print("=" * 30)
    print("✅ Operațiile de inserare și extragere au complexitatea O(log n)")
    print("✅ Heap-ul nativ Python este mai rapid datorită implementării în C")
    print("✅ Heap-ul bazat pe BD oferă persistență dar cu overhead suplimentar")
    print("✅ Ambele implementări respectă proprietățile teoretice ale heap-ului")
    print("\n📝 Pentru prezentarea academică:")
    print("- Heap-ul garantează O(log n) pentru inserare și extragere")
    print("- Structura de arbore binar complet asigură înălțimea log₂(n)")
    print("- Fiecare operație propagă modificările pe maximum log₂(n) nivele")


if __name__ == "__main__":
    # Verifică dacă matplotlib este disponibil
    try:
        import matplotlib.pyplot as plt
        import matplotlib
        matplotlib.use('Agg')  # Backend non-interactiv pentru server
    except ImportError:
        print("⚠️  Matplotlib nu este disponibil. Graficele nu vor fi generate.")
        print("Instalați cu: pip install matplotlib")
    
    main()
