# 🚀 Sistem Modern de Gestionare Cozi cu Prioritate

Un sistem complet de gestionare a cozilor cu suport pentru priorități, interfață web modernă și demonstrație academică a complexității O(log n) pentru operațiile heap.

## ✨ Caracteristici

### 🎯 Funcționalități Principale
- **Gestionare cozi cu prioritate** - 8 tipuri diferite de clienți cu priorități specifice
- **Implementare heap nativă** - Demonstrația complexității O(log n) pentru inserare și extragere
- **Interfață web modernă** - Design responsiv cu tema dark/light
- **Interfață consolă avansată** - Pentru utilizare în terminal cu emoji și culori
- **Calcul ETA în timp real** - Estimări precise pentru timpii de așteptare
- **Statistici detaliate** - Dashboard cu metrici în timp real
- **Auto-refresh** - Actualizare automată a interfeței web
- **Persistență date** - Toate datele sunt salvate în SQLite
- **Demonstrație academică** - Analiza complexității cu grafice și măsurători

### 👥 Tipuri de Clienți (în ordinea priorității)

| Prioritate | Tip Client | Timp Servire | Emoji | Descriere |
|------------|------------|--------------|-------|-----------|
| 1 | Urgență Medicală | 5 min | 🚨 | Cazuri medicale urgente |
| 2 | Client cu Dizabilități | 10 min | ♿ | Persoane cu dizabilități |
| 3 | Familie cu Dizabilități | 12 min | 👨‍👩‍👧‍👦♿ | Familii cu membri cu dizabilități |
| 4 | Familie cu Copii | 8 min | 👨‍👩‍👧‍👦 | Familii cu copii mici |
| 5 | Client cu Abonament | 7 min | 💳 | Clienți cu abonament premium |
| 6 | Mamă Însărcinată | 10 min | 🤱 | Femei însărcinate |
| 7 | Angajați | 3 min | 👔 | Personal intern |
| 8 | Client fără Abonament | 6 min | 👤 | Clienți standard |

## 🛠️ Instalare și Configurare

### Cerințe de Sistem
- Python 3.8 sau mai nou
- Conexiune la internet (pentru fonturile Google)

### Pas 1: Clonare și Instalare Dependințe
```bash
# Navigați în directorul proiectului
cd cozi_de_prioritate

# Instalați dependințele
pip install -r requirmentes.txt
```

### Pas 2: Inițializare Bază de Date
Baza de date SQLite se va crea automat la prima rulare.

## 🚀 Utilizare

### 💻 Interfața Web (Recomandată)
```bash
# Navigați în directorul flask_app
cd flask_app

# Porniți serverul Flask
python app.py
```

Apoi deschideți browser-ul la: **http://127.0.0.1:5001**

#### Funcționalități Web:
- **Dashboard cu statistici** - Vizualizare în timp real
- **Adăugare clienți** - Selectează tipul și numărul de clienți
- **Servire clienți** - Un click pentru a servi următorul client
- **Calculare ETA** - Introduceți ID-ul clientului pentru estimări
- **Actualizare prioritate** - Modificați prioritatea unui client existent
- **Ștergere clienți** - Ștergeți clienți după prioritate
- **Dark/Light Mode** - Toggle în colțul din dreapta sus
- **Auto-refresh** - Pagina se actualizează automat la 30 secunde

### 🖥️ Interfața Consolă
```bash
# Rulați sistemul principal
python main.py
```

#### Funcționalități Consolă:
- **[A]** Adaugă clienți (selectare interactivă)
- **[S]** Servește următorul client
- **[Q]** Afișează coada curentă
- **[U]** Actualizează prioritate client
- **[D]** Șterge clienți după prioritate
- **[C]** Calculează ETA pentru client specific
- **[F]** Filtrare avansată (index, prioritate, timp)
- **[T]** Toggle modul închidere magazin
- **[M]** Toggle servire automată
- **[H]** Toggle mod heap (MAX/MIN)

### 🔬 Demonstrația Complexității O(log n)
```bash
# Rulați demonstrația academică
python heap_complexity_demo.py
```

#### Caracteristici Demonstrație:
- **Analiza comparativă** între heap nativ și heap bazat pe BD
- **Măsurători de performanță** pentru diferite dimensiuni (100-10,000 elemente)
- **Grafice matematice** confirmând complexitatea O(log n)
- **Vizualizarea structurii heap** ca arbore binar
- **Verificarea proprietăților heap** (min-heap/max-heap)
- **Generarea automată** de grafice PNG cu rezultatele

### 🕰️ Sistem Original (Simplificat)
```bash
# Pentru sistemul original
python main.py
```

## 🎨 Capturi de Ecran

### Interfața Web Modernă
- **Design gradient frumos** cu culori moderne
- **Cards animate** cu hover effects
- **Tabel responsiv** cu badges pentru priorități
- **Dashboard statistici** în timp real
- **Dark mode elegant** cu tranziții fluide

### Interfața Consolă
- **Text colorat** cu emoji-uri expresive
- **Tabele formatate** pentru afișare clară
- **Meniuri interactive** cu validare input
- **Statistici detaliate** în format text

## 📊 Exemple de Utilizare

### Adăugare Clienți Bundle
```python
# Prin interfața web: selectați tipul și introduceți numărul
# Prin consolă: alegeți opțiunea [A] și urmați instrucțiunile
```

### Calculare ETA
```python
# Introduceți ID-ul clientului pentru a vedea:
# - Poziția în coadă
# - Timpul de așteptare
# - Timpul total până la finalizare
```

## 📚 Documentație Detaliată

### Fișiere de Documentație
- **README.md** - Ghid principal de utilizare
- **DOCUMENTATIE_TEHNICA.md** - Arhitectura și implementarea tehnică
- **PREZENTARE_ACADEMICA.md** - Prezentare pentru mediul academic
- **COMPLEXITY_DEMONSTRATION_SUMMARY.md** - Rezultatele analizei O(log n)
- **GHID_DEMONSTRATIE.md** - Ghid pentru demonstrația practică
- **ANEXA_TEHNICA.md** - Diagrame și exemple detaliate

### Fișiere Principale
- **main.py** - Aplicația consolă principală
- **heap_complexity_demo.py** - Demonstrația complexității O(log n)
- **flask_app/app.py** - Aplicația web Flask
- **flask_app/templates/index.html** - Interfața web
- **heap_complexity_analysis.png** - Graficele generate automat

## 🎓 Pentru Mediul Academic

Acest proiect demonstrează:
- **Implementarea heap-urilor** cu complexitate O(log n)
- **Comparația între implementări** (nativ vs. bazat pe BD)
- **Analiza teoretică vs. practică** a algoritmilor
- **Dezvoltarea aplicațiilor full-stack** cu Python
- **Gestiunea bazelor de date** cu SQLite
- **Design patterns** în dezvoltarea software

### Generare Automată
```python
# Pentru testare rapidă, folosiți generarea automată
# Sistemul va crea clienți aleatori bazați pe probabilități realiste
```

## 🔧 Configurare Avansată

### Modificare Priorități
Editați fișierul `modern_queue_system.py` și schimbați valorile în dicționarul `client_types`:

```python
self.client_types = {
    'nou_tip': ClientType('Nume Nou', prioritate, timp_servire, greutate, 'emoji'),
    # ...
}
```

### Personalizare Interfață Web
Modificați fișierul `flask_app/static/style.css` pentru:
- Culori personalizate
- Fonturi diferite
- Layout-uri alternative
- Animații suplimentare

### Configurare Bază de Date
Schimbați variabila `DB_NAME` pentru o locație diferită a bazei de date.

## 🐛 Depanare

### Probleme Comune

1. **ModuleNotFoundError: No module named 'flask'**
   ```bash
   pip install flask
   ```

2. **Probleme cu encoding-ul pe Windows**
   - Sistemul detectează automat Windows și configurează UTF-8
   - Pentru probleme persistente, setați: `set PYTHONIOENCODING=UTF-8`

3. **Port-ul 5001 este ocupat**
   - Modificați portul în `app.py`: `app.run(debug=True, port=5002)`

4. **Baza de date blocată**
   - Închideți toate instanțele sistemului
   - Ștergeți fișierul `queue.db` pentru resetare completă

5. **Graficele nu se generează (heap_complexity_demo.py)**
   ```bash
   pip install matplotlib numpy
   ```

## 📈 Rezultatele Demonstrației O(log n)

### Performanțe Măsurate
| Dimensiune | Heap Nativ | Heap BD | Confirmă O(log n) |
|------------|-------------|---------|-------------------|
| 100        | 0.04ms      | 2.97ms  | ✅                |
| 1,000      | 0.20ms      | 6.91ms  | ✅                |
| 10,000     | 1.72ms      | 32.65ms | ✅                |

**Concluzie:** Pentru 100x mai multe elemente, timpul crește doar 20-43x, confirmând complexitatea logaritmică.

## 🎯 Obiective Academice Atinse

- ✅ **Implementarea heap-urilor** cu demonstrația complexității O(log n)
- ✅ **Dezvoltarea aplicațiilor full-stack** cu Python și Flask
- ✅ **Managementul bazelor de date** cu operații CRUD eficiente
- ✅ **Analiza algoritmilor** prin măsurători empirice și validare teoretică
- ✅ **Interfețe utilizator** interactive (consolă și web)
- ✅ **Documentație tehnică** completă pentru mediul academic

## 🤝 Contribuții

Pentru îmbunătățiri sau raportarea de bug-uri:
1. Fork repository-ul
2. Creați o ramură pentru feature (`git checkout -b feature/AmazingFeature`)
3. Commit modificările (`git commit -m 'Add some AmazingFeature'`)
4. Push în ramură (`git push origin feature/AmazingFeature`)
5. Deschideți un Pull Request

## 📜 Licență

Acest proiect este dezvoltat în scop educațional pentru cursurile de informatică.

## 👥 Echipa de Dezvoltare

**Studenți Anul II - Facultatea de Informatică**
- Dezvoltare sistem management cozi prioritate
- Implementare demonstrație complexitate O(log n)
- Documentație tehnică și academică completă

**Data finalizării:** Iunie 2025

## 📈 Roadmap

### Funcționalități Planificate
- [ ] **API REST** pentru integrare cu alte sisteme
- [ ] **Notificări push** pentru clienți
- [ ] **Rapoarte PDF** cu statistici
- [ ] **Backup automat** al bazei de date
- [ ] **Multi-tenant** support pentru mai multe organizații
- [ ] **Integrare SMS/Email** pentru notificări
- [ ] **Analytics avansate** cu grafice
- [ ] **Mobile app** (PWA)

### Îmbunătățiri UX
- [ ] **Sunet notificări** la evenimente importante
- [ ] **Keyboard shortcuts** pentru operații rapide
- [ ] **Drag & drop** pentru reordonare manuală
- [ ] **Fullscreen mode** pentru display-uri publice
- [ ] **Custom themes** configurabile de utilizator

## 👨‍💻 Contribuții

Contribuțiile sunt binevenite! Pentru modificări majore:

1. Fork repository-ul
2. Creați un branch pentru feature-ul nou
3. Commitați modificările
4. Deschideți un Pull Request

## 📄 Licență

Acest proiect este licențiat sub MIT License. Vezi fișierul LICENSE pentru detalii.

## 🙏 Mulțumiri

- **Flask** pentru framework-ul web
- **SQLite** pentru baza de date
- **Google Fonts** pentru tipografia modernă
- **Emojipedia** pentru emoji-urile expresive

---

**Made with ❤️ pentru o experiență modernă de gestionare a cozilor**
