"""
GUI interface for the air quality monitoring application.
Provides a user-friendly interface to interact with air quality data.
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
import json
import sys
import locale

# Set proper encoding for Polish characters
try:
    locale.setlocale(locale.LC_ALL, 'pl_PL.UTF-8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'Polish_Poland.1250')
    except:
        print("Warning: Could not set Polish locale, but continuing anyway...")

# Fix for Windows console encoding
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Import your modules
from air_quality.api import GiosApi
from air_quality.database import AirQualityDatabase
from air_quality.dataanalysis import AirQualityAnalyzer
from air_quality.visualization import DataVisualizer


class ImportHistoryWindow:
    """Separate window to display import history."""
    
    def __init__(self, parent, app):
        self.parent = parent
        self.app = app
        self.window = None
        self.create_window()
    
    def create_window(self):
        """Create the import history window."""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Historia Importów Danych")
        self.window.geometry("500x400")
        self.window.transient(self.parent)  # Set as transient window
        self.window.grab_set()  # Make modal
        
        # Configure grid
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(1, weight=1)
        
        # Header
        header_frame = ttk.Frame(self.window, padding="10")
        header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        ttk.Label(
            header_frame, 
            text="Historia Importów Danych", 
            font=("Arial", 14, "bold")
        ).grid(row=0, column=0, sticky=tk.W)
        
        # Refresh button
        ttk.Button(
            header_frame, 
            text="Odśwież", 
            command=self.refresh_data
        ).grid(row=0, column=1, sticky=tk.E)
        
        # Main content frame
        content_frame = ttk.Frame(self.window, padding="10")
        content_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        content_frame.columnconfigure(0, weight=1)
        
        # Last import info
        last_import_frame = ttk.LabelFrame(content_frame, text="Ostatni Import", padding="10")
        last_import_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        last_import_frame.columnconfigure(1, weight=1)
        
        self.last_import_var = tk.StringVar(value="Brak danych")
        ttk.Label(last_import_frame, text="Data i godzina:").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(last_import_frame, textvariable=self.last_import_var, font=("Arial", 10, "bold")).grid(row=0, column=1, sticky=tk.W)
        
        self.time_ago_var = tk.StringVar(value="Brak danych")
        ttk.Label(last_import_frame, text="Czas temu:").grid(row=1, column=0, sticky=tk.W)
        ttk.Label(last_import_frame, textvariable=self.time_ago_var).grid(row=1, column=1, sticky=tk.W)
        
        # Statistics frame
        stats_frame = ttk.LabelFrame(content_frame, text="Statystyki", padding="10")
        stats_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        stats_frame.columnconfigure(1, weight=1)
        
        self.stations_var = tk.StringVar(value="0")
        ttk.Label(stats_frame, text="Wczytane stacje:").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(stats_frame, textvariable=self.stations_var).grid(row=0, column=1, sticky=tk.W)
        
        self.measurements_var = tk.StringVar(value="0")
        ttk.Label(stats_frame, text="Aktualne pomiary:").grid(row=1, column=0, sticky=tk.W)
        ttk.Label(stats_frame, textvariable=self.measurements_var).grid(row=1, column=1, sticky=tk.W)
        
        self.sensors_var = tk.StringVar(value="0")
        ttk.Label(stats_frame, text="Aktywne czujniki:").grid(row=2, column=0, sticky=tk.W)
        ttk.Label(stats_frame, textvariable=self.sensors_var).grid(row=2, column=1, sticky=tk.W)
        
        # Import history log
        log_frame = ttk.LabelFrame(content_frame, text="Historia Operacji", padding="10")
        log_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.history_text = scrolledtext.ScrolledText(log_frame, width=60, height=10)
        self.history_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Buttons frame
        buttons_frame = ttk.Frame(content_frame)
        buttons_frame.grid(row=3, column=0, sticky=(tk.W, tk.E))
        
        ttk.Button(buttons_frame, text="Zamknij", command=self.window.destroy).grid(row=0, column=1, sticky=tk.E)
        ttk.Button(buttons_frame, text="Wyczyść historię", command=self.clear_history).grid(row=0, column=0, sticky=tk.W)
        
        # Initialize data
        self.refresh_data()
        
        # Auto-refresh every 30 seconds
        self.auto_refresh()
    
    def refresh_data(self):
        """Refresh the data in the window."""
        # Update last import info
        if self.app.last_import_time:
            time_str = self.app.last_import_time.strftime("%Y-%m-%d %H:%M:%S")
            time_ago = self.app.get_time_ago_str(self.app.last_import_time)
            self.last_import_var.set(time_str)
            self.time_ago_var.set(time_ago)
        else:
            self.last_import_var.set("Brak danych")
            self.time_ago_var.set("Brak danych")
        
        # Update statistics
        self.stations_var.set(str(len(self.app.stations)))
        self.measurements_var.set(str(len(self.app.current_measurements) if self.app.current_measurements else 0))
        self.sensors_var.set(str(len(self.app.current_sensors) if self.app.current_sensors else 0))
        
        # Update history log
        self.update_history_log()
    
    def update_history_log(self):
        """Update the history log text."""
        self.history_text.delete(1.0, tk.END)
        
        if not self.app.import_history:
            self.history_text.insert(tk.END, "Brak historii operacji.\n")
            self.history_text.insert(tk.END, "Importuj dane, aby zobaczyć historię.")
            return
        
        for i, entry in enumerate(reversed(self.app.import_history[-100:])):
            time_str = entry['timestamp'].strftime("%H:%M:%S")
            self.history_text.insert(tk.END, f"{time_str} - {entry['operation']}\n")
            if entry.get('details'):
                self.history_text.insert(tk.END, f"    {entry['details']}\n")
            self.history_text.insert(tk.END, "\n")
    
    def clear_history(self):
        """Clear the import history."""
        if messagebox.askyesno("Wyczyść historię", "Czy na pewno chcesz wyczyścić historię operacji?"):
            self.app.import_history = []
            self.update_history_log()
            messagebox.showinfo("Sukces", "Historia operacji została wyczyszczona.")
    
    def auto_refresh(self):
        """Auto-refresh the window every 30 seconds."""
        self.refresh_data()
        self.window.after(30000, self.auto_refresh)  # Refresh every 30 seconds


class AirQualityApp:
    """Main application class for the air quality monitoring GUI."""

    def __init__(self, root: tk.Tk):
        """
        Initialize the air quality application.
        """
        self.root = root
        self.root.title("Monitor Jakości Powietrza w Polsce - GIOŚ")
        self.root.geometry("1000x700")

        # Initialize components
        self.api = GiosApi()
        
        # Initialize database with better error handling
        self.db = None
        try:
            self.db = AirQualityDatabase()
            if self.db.conn is None:
                print("Database connection failed, continuing without database")
        except Exception as e:
            print(f"Database initialization failed: {e}")
            # Continue without database - we'll use API directly

        self.analyzer = AirQualityAnalyzer()
        self.visualizer = DataVisualizer()

        # Data storage
        self.stations: List[Dict[str, Any]] = []
        self.current_station: Optional[Dict[str, Any]] = None
        self.current_sensors: List[Dict[str, Any]] = []
        self.current_measurements: List[Dict[str, Any]] = []
        
        # Track last import time and history
        self.last_import_time: Optional[datetime] = None
        self.import_history: List[Dict[str, Any]] = []
        
        # Import history window reference
        self.import_history_window = None

        # Create GUI
        self.create_widgets()
        self.create_menu()

        # Load initial data
        self.load_initial_data()

    # ───────────────────────────── GUI ELEMENTS ───────────────────────────── #

    def create_widgets(self):
        """Create and arrange all GUI widgets."""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # Station selection frame
        station_frame = ttk.LabelFrame(main_frame, text="Wybierz stację", padding="5")
        station_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        station_frame.columnconfigure(1, weight=1)

        ttk.Label(station_frame, text="Sposób wyszukiwania:").grid(row=0, column=0, sticky=tk.W, pady=5)

        self.search_method = tk.StringVar(value="all")
        ttk.Radiobutton(
            station_frame, text="Wszystkie stacje",
            variable=self.search_method, value="all",
            command=self.on_search_method_change
        ).grid(row=0, column=1, sticky=tk.W)

        ttk.Radiobutton(
            station_frame, text="Według miasta",
            variable=self.search_method, value="city",
            command=self.on_search_method_change
        ).grid(row=0, column=2, sticky=tk.W)

        self.city_frame = ttk.Frame(station_frame)
        self.city_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        self.city_frame.grid_remove()  # Hide initially

        ttk.Label(self.city_frame, text="Nazwa miasta:").grid(row=0, column=0, sticky=tk.W)
        self.city_var = tk.StringVar()
        city_entry = ttk.Entry(self.city_frame, textvariable=self.city_var, width=20)
        city_entry.grid(row=0, column=1, padx=5)
        ttk.Button(self.city_frame, text="Szukaj", command=self.search_by_city).grid(row=0, column=2)

        # Stations listbox
        ttk.Label(station_frame, text="Dostępne stacje:").grid(row=2, column=0, sticky=tk.W, pady=(10, 0))

        self.stations_listbox = tk.Listbox(station_frame, height=6, width=50)
        self.stations_listbox.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        self.stations_listbox.bind('<<ListboxSelect>>', self.on_station_select)

        # Sensors frame
        sensors_frame = ttk.LabelFrame(main_frame, text="Czujniki stacji", padding="5")
        sensors_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        sensors_frame.columnconfigure(0, weight=1)
        sensors_frame.rowconfigure(0, weight=1)

        self.sensors_tree = ttk.Treeview(
            sensors_frame, columns=("param", "formula", "code", "concentration"),
            show="headings", height=6
        )
        self.sensors_tree.heading("param", text="Parametr")
        self.sensors_tree.heading("formula", text="Symbol")
        self.sensors_tree.heading("code", text="Kod")
        self.sensors_tree.heading("concentration", text="Stężenie [μg/m³]")
        self.sensors_tree.column("param", width=150)
        self.sensors_tree.column("formula", width=80)
        self.sensors_tree.column("code", width=80)
        self.sensors_tree.column("concentration", width=120)

        sensors_scrollbar = ttk.Scrollbar(sensors_frame, orient=tk.VERTICAL, command=self.sensors_tree.yview)
        self.sensors_tree.configure(yscrollcommand=sensors_scrollbar.set)

        self.sensors_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        sensors_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.sensors_tree.bind('<<TreeviewSelect>>', self.on_sensor_select)

        # Measurements frame
        measurements_frame = ttk.LabelFrame(main_frame, text="Dane pomiarowe", padding="5")
        measurements_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0), pady=5)
        measurements_frame.columnconfigure(0, weight=1)
        measurements_frame.rowconfigure(1, weight=1)

        # Date range and import info frame
        date_frame = ttk.Frame(measurements_frame)
        date_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(date_frame, text="Od:").grid(row=0, column=0, sticky=tk.W)
        self.start_date = tk.StringVar(value=(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'))
        ttk.Entry(date_frame, textvariable=self.start_date, width=10).grid(row=0, column=1, padx=5)

        ttk.Label(date_frame, text="Do:").grid(row=0, column=2, sticky=tk.W, padx=(10, 0))
        self.end_date = tk.StringVar(value=datetime.now().strftime('%Y-%m-%d'))
        ttk.Entry(date_frame, textvariable=self.end_date, width=10).grid(row=0, column=3, padx=5)

        ttk.Button(date_frame, text="Pobierz dane", command=self.fetch_measurements).grid(row=0, column=4, padx=10)
        ttk.Button(date_frame, text="Pokaż wykres", command=self.show_chart).grid(row=0, column=5)
        ttk.Button(date_frame, text="Debug API", command=self.debug_api_response).grid(row=0, column=6, padx=5)

        # Add Test Historical Data button
        ttk.Button(date_frame, text="Test danych historycznych", command=self.test_historical_data).grid(row=0, column=7, padx=5)

        # Last import info with button to open history window
        import_info_frame = ttk.Frame(date_frame)
        import_info_frame.grid(row=1, column=0, columnspan=8, sticky=(tk.W, tk.E), pady=(5, 0))
        
        self.last_import_var = tk.StringVar(value="Ostatni import: brak danych")
        last_import_label = ttk.Label(import_info_frame, textvariable=self.last_import_var, font=("Arial", 8))
        last_import_label.grid(row=0, column=0, sticky=tk.W)
        
        ttk.Button(
            import_info_frame, 
            text="Pokaż historię importów", 
            command=self.show_import_history,
            width=20
        ).grid(row=0, column=1, sticky=tk.E)

        self.measurements_text = scrolledtext.ScrolledText(measurements_frame, width=40, height=15)
        self.measurements_text.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        # Analysis frame
        analysis_frame = ttk.LabelFrame(main_frame, text="Analiza danych", padding="5")
        analysis_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        self.analysis_text = scrolledtext.ScrolledText(analysis_frame, width=100, height=8)
        self.analysis_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Status bar
        self.status_var = tk.StringVar(value="Gotowy")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

    def create_menu(self):
        """Create the application menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Plik", menu=file_menu)
        file_menu.add_command(label="Zapisz dane", command=self.save_current_data)
        file_menu.add_separator()
        file_menu.add_command(label="Zamknij", command=self.on_closing)

        data_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Dane", menu=data_menu)
        data_menu.add_command(label="Pobierz wszystkie stacje", command=self.fetch_stations_from_api)
        data_menu.add_command(label="Pokaż indeks jakości powietrza", command=self.show_air_quality_index)
        data_menu.add_separator()
        data_menu.add_command(label="Testuj dane historyczne", command=self.test_historical_data)
        data_menu.add_command(label="Pokaż historię importów", command=self.show_import_history)

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Pomoc", menu=help_menu)
        help_menu.add_command(label="O programie", command=self.show_about)

    # ───────────────────────────── HISTORICAL DATA TEST METHOD ───────────────────────────── #

    def test_historical_data(self):
        """Test historical data access from the GUI."""
        selection = self.sensors_tree.selection()
        if not selection:
            messagebox.showwarning("Ostrzeżenie", "Proszę wybrać czujnik.")
            return
            
        sensor_id = self.current_sensors[self.sensors_tree.index(selection[0])]['id']
        
        print("🚀 Testing historical data access...")
        results = self.api.test_historical_data_access(sensor_id)
        
        # Display results with better formatting
        self.analysis_text.delete(1.0, tk.END)
        self.analysis_text.insert(tk.END, "WYNIKI TESTU DANYCH HISTORYCZNYCH - GIOŚ API\n")
        self.analysis_text.insert(tk.END, "=" * 60 + "\n\n")
        
        # Display API limitations first
        if 'api_limitations' in results:
            limitations = results['api_limitations']
            self.analysis_text.insert(tk.END, "📋 OGRANICZENIA API GIOŚ:\n")
            for limitation in limitations.get('limitations', []):
                self.analysis_text.insert(tk.END, f"   • {limitation}\n")
            self.analysis_text.insert(tk.END, "\n")
        
        # Display test results
        for test_name, result in results.items():
            if test_name == 'api_limitations':
                continue
                
            self.analysis_text.insert(tk.END, f"🔍 {test_name}:\n")
            if result.get('success'):
                self.analysis_text.insert(tk.END, f"   ✅ Dane dostępne: {result['measurements_count']} pomiarów\n")
                self.analysis_text.insert(tk.END, f"   📅 Zakres dat: {result['date_range']}\n")
                if result.get('is_actually_historical') is False:
                    self.analysis_text.insert(tk.END, f"   ⚠️  Uwaga: {result.get('note', 'Dane mogą być tylko bieżące')}\n")
                else:
                    self.analysis_text.insert(tk.END, f"   💡 Informacja: {result.get('note', 'Dane historyczne')}\n")
            else:
                self.analysis_text.insert(tk.END, f"   ❌ Brak danych: {result.get('reason', 'Nieznany błąd')}\n")
                if 'note' in result:
                    self.analysis_text.insert(tk.END, f"   💡 {result['note']}\n")
            self.analysis_text.insert(tk.END, "\n")

    # ───────────────────────────── APP LOGIC ───────────────────────────── #

    def show_import_history(self):
        """Show the import history window."""
        if self.import_history_window is None or not self.import_history_window.window.winfo_exists():
            self.import_history_window = ImportHistoryWindow(self.root, self)
        else:
            self.import_history_window.window.lift()  # Bring to front
            self.import_history_window.window.focus_force()  # Focus the window

    def add_to_import_history(self, operation: str, details: str = ""):
        """Add an entry to the import history."""
        entry = {
            'timestamp': datetime.now(),
            'operation': operation,
            'details': details
        }
        self.import_history.append(entry)
        
        # Keep only last 50 entries to prevent memory issues
        if len(self.import_history) > 50:
            self.import_history = self.import_history[-50:]

    def update_last_import_time(self, operation: str = "Import danych", details: str = ""):
        """Update the last import time and refresh the display."""
        self.last_import_time = datetime.now()
        self.add_to_import_history(operation, details)
        self.update_last_import_display()

    def update_last_import_display(self):
        """Update the last import time display."""
        if self.last_import_time:
            time_str = self.last_import_time.strftime("%Y-%m-%d %H:%M:%S")
            self.last_import_var.set(f"Ostatni import: {time_str}")
        else:
            self.last_import_var.set("Ostatni import: brak danych")

    def get_time_ago_str(self, past_time: datetime) -> str:
        """Get human-readable string describing how long ago the time was."""
        now = datetime.now()
        diff = now - past_time
        
        if diff.days > 0:
            return f"{diff.days} dni temu"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"{hours} godzin temu"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            return f"{minutes} minut temu"
        else:
            return f"{diff.seconds} sekund temu"

    def on_search_method_change(self):
        """Handle search method radio button selection change."""
        method = self.search_method.get()
        
        # Show/hide city search frame based on selection
        if method == "city":
            self.city_frame.grid()  # Show city search
        else:
            self.city_frame.grid_remove()  # Hide city search
            self.load_all_stations()  # Load all stations when "all" is selected

    def load_all_stations(self):
        """Load all stations from database or API."""
        self.status_var.set("Ładowanie wszystkich stacji...")
        self.root.update()
        
        try:
            # First try to load from database if available
            if self.db and self.db.conn:
                cursor = self.db.conn.cursor()
                cursor.execute("SELECT id, stationName, city, addressStreet FROM stations ORDER BY city, stationName")
                db_stations = cursor.fetchall()
                
                if db_stations:
                    self.stations = []
                    for station in db_stations:
                        # FIX: Always include station even if city is missing
                        city_name = station['city'] if station['city'] else 'Nieznane miasto'
                        self.stations.append({
                            'id': station['id'],
                            'stationName': station['stationName'],
                            'city': {'name': city_name},  # Always create city dict
                            'addressStreet': station['addressStreet'] if 'addressStreet' in station.keys() else None
                        })
                    
                    # Update listbox - FIX: Ensure all stations are displayed
                    self.stations_listbox.delete(0, tk.END)
                    for station in self.stations:
                        # FIX: Simplified city extraction that always works
                        city_obj = station.get('city', {})
                        if isinstance(city_obj, dict):
                            display_city = city_obj.get('name', 'Nieznane miasto')
                        else:
                            display_city = str(city_obj) if city_obj else 'Nieznane miasto'
                        
                        display_text = f"{display_city} - {station['stationName']}"
                        self.stations_listbox.insert(tk.END, display_text)
                        
                    self.status_var.set(f"Załadowano {len(self.stations)} stacji z bazy danych")
                    self.add_to_import_history("Ładowanie stacji z bazy", f"{len(self.stations)} stacji")
                    return
            
            # If no database or no stations in DB, fetch from API
            self.fetch_stations_from_api()
            
        except Exception as e:
            self.status_var.set(f"Błąd ładowania stacji: {e}")
            # Fallback to API if database fails
            self.fetch_stations_from_api()

    def load_initial_data(self):
        """Load initial data when application starts."""
        self.load_all_stations()

    def search_by_city(self):
        """Search for stations by city name."""
        city_name = self.city_var.get().strip()
        if not city_name:
            messagebox.showwarning("Ostrzeżenie", "Proszę wprowadzić nazwę miasta.")
            return
            
        self.status_var.set(f"Wyszukiwanie stacji w mieście: {city_name}...")
        self.root.update()
        
        try:
            cursor = self.db.conn.cursor()
            cursor.execute(
                "SELECT id, stationName, city, addressStreet FROM stations WHERE city LIKE ? ORDER BY stationName",
                (f"%{city_name}%",)
            )
            stations = cursor.fetchall()
            
            if not stations:
                self.status_var.set(f"Brak stacji w mieście: {city_name}")
                messagebox.showinfo("Info", f"Nie znaleziono stacji w mieście: {city_name}")
                return
                
            self.stations = []
            self.stations_listbox.delete(0, tk.END)
            for station in stations:
                # FIX: Always include city information, even if empty
                city_name_db = station['city'] if station['city'] else 'Nieznane miasto'
                normalized = {
                    'id': station['id'],
                    'stationName': station['stationName'],
                    'city': {'name': city_name_db},  # Always create city dict
                    'addressStreet': station['addressStreet']
                }
                self.stations.append(normalized)

                display_text = f"{city_name_db} - {normalized['stationName']}"
                self.stations_listbox.insert(tk.END, display_text)
                
            self.status_var.set(f"Znaleziono {len(self.stations)} stacji w mieście: {city_name}")
            self.add_to_import_history("Wyszukiwanie stacji", f"Miasto: {city_name}, znaleziono: {len(self.stations)}")
            
        except Exception as e:
            self.status_var.set(f"Błąd wyszukiwania: {e}")
            messagebox.showerror("Błąd", f"Nie udało się wyszukać stacji: {e}")

    def on_station_select(self, event):
        """Handle station selection from listbox."""
        selection = self.stations_listbox.curselection()
        if not selection:
            return
            
        index = selection[0]
        if index < len(self.stations):
            self.current_station = self.stations[index]
            self.status_var.set(f"Wybrano stację: {self.current_station['stationName']}")
            self.load_sensors_for_station(self.current_station['id'])

    def load_sensors_for_station(self, station_id: int):
        """Load sensors for the selected station."""
        self.status_var.set("Ładowanie czujników...")
        self.root.update()
        
        try:
            # Clear previous sensors
            for item in self.sensors_tree.get_children():
                self.sensors_tree.delete(item)
                
            # Get sensors from API
            sensors = self.api.get_sensors_for_station(station_id)
            if sensors:
                self.current_sensors = sensors
                
                # First, add all sensors with "Ładowanie..." placeholder
                for sensor in sensors:
                    # Handle both old and new format
                    if 'param' in sensor and isinstance(sensor['param'], dict):
                        # New format (converted from Polish)
                        param_name = sensor['param'].get('paramName', 'Nieznany')
                        param_formula = sensor['param'].get('paramFormula', '')
                        param_code = sensor['param'].get('paramCode', '')
                    else:
                        # Old format (direct from API)
                        param_name = sensor.get('param', {}).get('paramName', 'Nieznany')
                        param_formula = sensor.get('param', {}).get('paramFormula', '')
                        param_code = sensor.get('param', {}).get('paramCode', '')
                    
                    # Add sensor with loading placeholder
                    self.sensors_tree.insert("", "end", values=(param_name, param_formula, param_code, "Ładowanie..."))
                
                # Now update concentrations in background (non-blocking)
                self.root.after(100, lambda: self.update_all_concentrations(sensors))
                    
                self.status_var.set(f"Załadowano {len(sensors)} czujników")
                self.add_to_import_history("Ładowanie czujników", f"{len(sensors)} czujników")
            else:
                self.status_var.set("Brak czujników dla wybranej stacji")
                
        except Exception as e:
            self.status_var.set(f"Błąd ładowania czujników: {e}")
            messagebox.showerror("Błąd", f"Nie udało się załadować czujników: {e}")
            print(f"Sensor loading error: {e}")
            import traceback
            traceback.print_exc()

    def update_all_concentrations(self, sensors: List[Dict[str, Any]]):
        """Update concentration values for all sensors."""
        try:
            items = self.sensors_tree.get_children()
            
            for i, sensor in enumerate(sensors):
                if i < len(items):
                    concentration = self.get_current_concentration(sensor.get('id'))
                    
                    # Get current values
                    current_values = self.sensors_tree.item(items[i], 'values')
                    if current_values and len(current_values) >= 3:
                        # Update only the concentration column
                        new_values = (current_values[0], current_values[1], current_values[2], concentration)
                        self.sensors_tree.item(items[i], values=new_values)
                    
                    # Small delay to avoid overwhelming the API
                    self.root.update_idletasks()
                    
        except Exception as e:
            print(f"Error updating concentrations: {e}")

    def get_current_concentration(self, sensor_id: int) -> str:
        """Get current concentration value for a sensor - MOST RECENT measurement."""
        try:
            if not sensor_id:
                return "Brak ID"

            # First try cached data from the database
            if self.db and self.db.conn:
                cached = self.db.get_measurements(sensor_id)
                converted = self._convert_db_rows_to_measurements(cached)
                if converted:
                    return f"{converted[0]['value']:.2f}"

            # Fall back to live API data
            raw_data = self.api.get_measurements_for_sensor(sensor_id)
            measurements = self.api.process_measurement_data(raw_data) if raw_data else []

            if measurements:
                if self.db and self.db.conn:
                    station_id = self.current_station['id'] if self.current_station else None
                    sensor_meta = next((s for s in self.current_sensors if s.get('id') == sensor_id), None)
                    self.db.save_measurements(
                        sensor_id,
                        measurements,
                        station_id=station_id,
                        param_code=self._get_sensor_param_code(sensor_meta)
                    )
                return f"{measurements[0]['value']:.2f}"

            return "Brak danych"

        except Exception as e:
            print(f"Error getting concentration for sensor {sensor_id}: {e}")
            return f"Błąd: {str(e)[:15]}"

    def debug_sensor_data(self):
        """Debug method to check what data we're getting from API."""
        if not self.current_sensors:
            messagebox.showwarning("Debug", "No sensors loaded")
            return
        
        print("=== DEBUG SENSOR DATA ===")
        for i, sensor in enumerate(self.current_sensors):
            sensor_id = sensor.get('id')
            print(f"Sensor {i}: ID={sensor_id}, Data={sensor}")
            
            if sensor_id:
                try:
                    raw_data = self.api.get_measurements_for_sensor(sensor_id)
                    print(f"Raw API response for sensor {sensor_id}:")
                    print(f"Type: {type(raw_data)}")
                    if isinstance(raw_data, dict):
                        print("Keys:", list(raw_data.keys()))
                    elif isinstance(raw_data, list):
                        print(f"List length: {len(raw_data)}")
                    print(f"Data: {raw_data}")
                    print("-" * 50)
                    
                except Exception as e:
                    print(f"Error: {e}")
        
        print("=== END DEBUG ===")
        messagebox.showinfo("Debug", "Check console for debug information")

    def debug_api_response(self, sensor_id: int = None):
        """Debug method to check API response structure."""
        if not sensor_id:
            selection = self.sensors_tree.selection()
            if not selection:
                messagebox.showwarning("Debug", "Proszę wybrać czujnik")
                return
            item = selection[0]
            sensor_index = self.sensors_tree.index(item)
            if sensor_index >= len(self.current_sensors):
                return
            sensor = self.current_sensors[sensor_index]
            sensor_id = sensor['id']
        
        try:
            print("=== DEBUG API RESPONSE ===")
            raw_data = self.api.get_measurements_for_sensor(sensor_id)
            print(f"Raw API response type: {type(raw_data)}")
            
            if isinstance(raw_data, dict):
                print("Keys:", list(raw_data.keys()))
                # Check for datetime objects in the response
                for key, value in raw_data.items():
                    if isinstance(value, datetime):
                        print(f"Found datetime object in key '{key}': {value}")
            
            print("=== END DEBUG ===")
            
        except Exception as e:
            print(f"Debug error: {e}")

    def on_sensor_select(self, event):
        """Handle sensor selection from treeview."""
        selection = self.sensors_tree.selection()
        if not selection:
            return
            
        item = selection[0]
        values = self.sensors_tree.item(item, 'values')
        if values and self.current_sensors:
            sensor_index = self.sensors_tree.index(item)
            if sensor_index < len(self.current_sensors):
                sensor = self.current_sensors[sensor_index]
                sensor_name = values[0]  # paramName from treeview
                concentration = values[3] if len(values) > 3 else "Brak danych"
                self.status_var.set(f"Wybrano czujnik: {sensor_name} (Stężenie: {concentration})")

    def fetch_measurements(self):
        """Fetch measurements for selected sensor."""
        selection = self.sensors_tree.selection()
        if not selection or not self.current_station:
            messagebox.showwarning("Ostrzeżenie", "Proszę wybrać stację i czujnik.")
            return
            
        item = selection[0]
        sensor_index = self.sensors_tree.index(item)
        if sensor_index >= len(self.current_sensors):
            return
            
        sensor = self.current_sensors[sensor_index]
        sensor_id = sensor['id']
        
        # Get the selected date range for informational purposes
        try:
            start_date = datetime.strptime(self.start_date.get(), '%Y-%m-%d')
            end_date = datetime.strptime(self.end_date.get(), '%Y-%m-%d')
            if start_date > end_date:
                messagebox.showwarning("Ostrzeżenie", "Data początkowa nie może być późniejsza niż data końcowa.")
                return
                
        except ValueError as e:
            messagebox.showerror("Błąd", f"Nieprawidłowy format daty: {e}")
            return

        start_dt = start_date
        end_dt = end_date + timedelta(days=1) - timedelta(seconds=1)
        requested_label = f"{start_date.strftime('%Y-%m-%d')} - {end_date.strftime('%Y-%m-%d')}"

        self.status_var.set("Pobieranie danych pomiarowych...")
        self.root.update()

        processed_data: List[Dict[str, Any]] = []
        data_source = None
        api_refreshed = False

        if self.db and self.db.conn:
            db_rows = self.db.get_measurements(sensor_id, start_date=start_dt, end_date=end_dt)
            processed_data = self._convert_db_rows_to_measurements(db_rows)
            if processed_data:
                data_source = "baza danych"

        api_refreshed = False

        try:
            if not processed_data:
                raw_data = self.api.get_measurements_for_sensor(
                    sensor_id,
                    start_date=start_date.strftime('%Y-%m-%d'),
                    end_date=end_date.strftime('%Y-%m-%d')
                )
                processed_from_api = self.api.process_measurement_data(raw_data) if raw_data else []
                api_refreshed = bool(processed_from_api)

                if processed_from_api:
                    if self.db and self.db.conn:
                        inserted = self.db.save_measurements(
                            sensor_id,
                            processed_from_api,
                            station_id=self.current_station.get('id'),
                            param_code=self._get_sensor_param_code(sensor)
                        )
                        if inserted:
                            db_rows = self.db.get_measurements(sensor_id, start_date=start_dt, end_date=end_dt)
                            processed_data = self._convert_db_rows_to_measurements(db_rows)
                            data_source = "baza danych"

                    if not processed_data:
                        processed_data = self._filter_measurements_by_range(processed_from_api, start_dt, end_dt)
                        if processed_data:
                            latest = processed_data[0]['date']
                            earliest = processed_data[-1]['date']
                            if earliest and earliest <= start_dt and latest and latest >= end_dt:
                                data_source = "API (pełny zakres)"
                            else:
                                data_source = "API (ograniczony zakres)"
                        else:
                            data_source = "API (ograniczony zakres)"
                else:
                    processed_data = []
                    data_source = None

            self._display_measurements(
                processed_data,
                sensor_index,
                sensor_id,
                requested_label,
                data_source or "brak danych",
                api_refreshed=api_refreshed
            )

        except Exception as exc:
            self.status_var.set(f"Błąd pobierania danych: {exc}")
            messagebox.showerror("Błąd", f"Nie udało się pobrać danych: {exc}")
            print(f"Measurement fetching error: {exc}")
            import traceback
            traceback.print_exc()

    def _get_sensor_param_code(self, sensor: Dict[str, Any]) -> Optional[str]:
        """Extract parameter code from sensor definition."""
        if not isinstance(sensor, dict):
            return None
        param = sensor.get('param')
        if isinstance(param, dict):
            return param.get('paramCode') or param.get('code')
        return None

    def _convert_db_rows_to_measurements(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert database rows into the measurement structure used by the UI."""
        prepared: List[Dict[str, Any]] = []
        for row in rows:
            if not isinstance(row, dict):
                continue

            date_value = row.get('date')
            if date_value is None and row.get('raw_date'):
                try:
                    date_value = datetime.strptime(row['raw_date'], '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    try:
                        date_value = datetime.fromisoformat(row['raw_date'])
                    except Exception:
                        date_value = None

            prepared.append({
                'date': date_value,
                'value': row.get('value')
            })

        prepared = [item for item in prepared if item['date'] is not None and item['value'] is not None]
        prepared.sort(key=lambda x: x['date'], reverse=True)
        return prepared

    def _filter_measurements_by_range(
        self,
        measurements: List[Dict[str, Any]],
        start_dt: datetime,
        end_dt: datetime
    ) -> List[Dict[str, Any]]:
        """Filter API measurements by requested datetime range."""
        filtered: List[Dict[str, Any]] = []
        for item in measurements:
            dt = item.get('date')
            value = item.get('value')
            if dt is None or value is None:
                continue
            if start_dt <= dt <= end_dt:
                filtered.append({'date': dt, 'value': value})

        filtered.sort(key=lambda x: x['date'], reverse=True)
        return filtered

    def _display_measurements(
        self,
        measurements: List[Dict[str, Any]],
        sensor_index: int,
        sensor_id: int,
        requested_label: str,
        data_source: str,
        *,
        api_refreshed: bool = False
    ):
        """Render measurements and analysis in the UI and update metadata."""

        ordered_measurements = sorted(
            [m for m in measurements if m.get('date') and m.get('value') is not None],
            key=lambda x: x['date'],
            reverse=True
        )
        self.current_measurements = ordered_measurements

        self.measurements_text.delete(1.0, tk.END)

        if not ordered_measurements:
            message = (
                f"Brak danych dla żądanego zakresu ({requested_label}).\n"
                f"Źródło: {data_source}. Spróbuj pobrać dane ponownie później."
            )
            self.measurements_text.insert(tk.END, message)
            analysis = self.analyzer.analyze_measurements([])
            self.display_analysis(analysis)
            self.status_var.set("Brak danych w wybranym zakresie")
            return

        actual_dates = [m['date'] for m in ordered_measurements]
        min_date = min(actual_dates)
        max_date = max(actual_dates)
        actual_range = f"{min_date.strftime('%Y-%m-%d %H:%M')} do {max_date.strftime('%Y-%m-%d %H:%M')}"

        header_lines = [
            f"ŻĄDANY zakres: {requested_label}",
            f"RZECZYWISTY zakres: {actual_range}",
            f"Liczba pomiarów: {len(ordered_measurements)}",
            f"Źródło danych: {data_source}"
        ]
        self.measurements_text.insert(tk.END, "\n".join(header_lines) + "\n" + "=" * 50 + "\n\n")

        for measurement in ordered_measurements:
            date_str = measurement['date'].strftime('%Y-%m-%d %H:%M:%S')
            value_str = f"{measurement['value']:.2f}"
            self.measurements_text.insert(tk.END, f"{date_str}: {value_str} μg/m³\n")

        analysis = self.analyzer.analyze_measurements(ordered_measurements)
        self.display_analysis(analysis)
        self.update_concentration_column(sensor_index, ordered_measurements)

        if api_refreshed:
            self.update_last_import_time(
                "Pobieranie danych pomiarowych",
                f"{len(ordered_measurements)} pomiarów z czujnika {sensor_id}"
            )
            status_suffix = "API (ograniczony zakres)" if "ograniczony" in data_source.lower() else "API"
            status_message = f"Pobrano {len(ordered_measurements)} pomiarów ({status_suffix})"
        else:
            self.add_to_import_history(
                "Wczytanie danych historycznych",
                f"{len(ordered_measurements)} pomiarów z czujnika {sensor_id}"
            )
            status_message = f"Załadowano {len(ordered_measurements)} pomiarów z bazy"

        self.status_var.set(status_message)

    def update_concentration_column(self, sensor_index: int, measurements: List[Dict[str, Any]]):
        """Update concentration column in the sensors treeview."""
        try:
            if measurements and len(measurements) > 0:
                # Weź najnowszy pomiar (pierwszy na liście po sortowaniu)
                latest_measurement = measurements[0]
                new_concentration = f"{latest_measurement['value']:.2f}"
                
                # Znajdź odpowiedni wiersz w treeview
                items = self.sensors_tree.get_children()
                if sensor_index < len(items):
                    item = items[sensor_index]
                    current_values = self.sensors_tree.item(item, 'values')
                    
                    # Zaktualizuj tylko kolumnę stężenia, zachowując pozostałe wartości
                    if len(current_values) >= 4:
                        new_values = (current_values[0], current_values[1], current_values[2], new_concentration)
                    else:
                        new_values = current_values + (new_concentration,)
                    
                    self.sensors_tree.item(item, values=new_values)
                    
        except Exception as e:
            print(f"Error updating concentration column: {e}")

    def display_analysis(self, analysis: Dict[str, Any]):
        """Display analysis results in the analysis text area."""
        self.analysis_text.delete(1.0, tk.END)
        
        if analysis['count'] == 0:
            self.analysis_text.insert(tk.END, "Brak danych do analizy.")
            return
            
        self.analysis_text.insert(tk.END, "ANALIZA DANYCH POMIAROWYCH\n")
        self.analysis_text.insert(tk.END, "=" * 40 + "\n\n")
        self.analysis_text.insert(tk.END, f"Liczba pomiarów: {analysis['count']}\n")
        self.analysis_text.insert(tk.END, f"Wartość minimalna: {analysis['min_value']:.2f} μg/m³\n")
        self.analysis_text.insert(tk.END, f"Wartość maksymalna: {analysis['max_value']:.2f} μg/m³\n")
        self.analysis_text.insert(tk.END, f"Średnia wartość: {analysis['avg_value']:.2f} μg/m³\n")
        self.analysis_text.insert(tk.END, f"Mediana: {analysis['median_value']:.2f} μg/m³\n")
        self.analysis_text.insert(tk.END, f"Odchylenie standardowe: {analysis['std_dev']:.2f} μg/m³\n")
        self.analysis_text.insert(tk.END, f"Zakres danych: {analysis['data_range']:.2f} μg/m³\n\n")
        
        self.analysis_text.insert(tk.END, f"Trend: {analysis['trend_direction']}\n")
        self.analysis_text.insert(tk.END, f"Siła trendu: {analysis['trend_strength']}\n\n")
        
        if analysis['min_date']:
            self.analysis_text.insert(tk.END, f"Data wartości min: {analysis['min_date']}\n")
        if analysis['max_date']:
            self.analysis_text.insert(tk.END, f"Data wartości max: {analysis['max_date']}\n")

    def show_chart(self):
        """Display chart for selected sensor data."""
        if not self.current_measurements:
            messagebox.showwarning("Ostrzeżenie", "Brak danych do wyświetlenia na wykresie.")
            return
            
        try:
            # Create a simple plot using matplotlib
            dates = [m['date'] for m in self.current_measurements]
            values = [m['value'] for m in self.current_measurements]
            
            plt.figure(figsize=(10, 6))
            plt.plot(dates, values, 'b-', marker='o', markersize=3)
            plt.title(f"Pomiary czujnika - {self.current_station['stationName']}")
            plt.xlabel("Data")
            plt.ylabel("Stężenie [μg/m³]")
            plt.xticks(rotation=45)
            plt.grid(True)
            plt.tight_layout()
            plt.show()
            
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się wyświetlić wykresu: {e}")

    def fetch_stations_from_api(self):
        """Fetch all stations from GIOŚ API and save to database."""
        self.status_var.set("Pobieranie stacji z API GIOŚ...")
        self.root.update()
        
        try:
            stations = self.api.get_stations()
            if not stations:
                self.status_var.set("Nie udało się pobrać stacji z API lub format danych jest nieprawidłowy")
                return

            # Save to database if available
            if self.db and self.db.conn:
                cursor = self.db.conn.cursor()
                cursor.execute("DELETE FROM stations")  # Clear existing data

                for station in stations:
                    station_id = station.get('id')
                    station_name = station.get('stationName') or 'Nieznana stacja'
                    city_name = None
                    if isinstance(station.get('city'), dict):
                        city_name = station['city'].get('name')
                    elif station.get('city'):
                        city_name = station.get('city')  # already string
                    city_name = city_name or 'Nieznane miasto'
                    address_street = station.get('addressStreet')

                    cursor.execute(
                        "INSERT INTO stations (id, stationName, city, addressStreet) VALUES (?, ?, ?, ?)",
                        (station_id, station_name, city_name, address_street)
                    )

                self.db.conn.commit()

            # Keep full station data in memory for subsequent operations
            self.stations = stations

            # Update listbox - FIX: Ensure all stations are displayed
            self.stations_listbox.delete(0, tk.END)
            for station in self.stations:
                # FIX: Handle city information more robustly
                city_data = station.get('city')
                if isinstance(city_data, dict):
                    city = city_data.get('name', 'Nieznane miasto')
                elif isinstance(city_data, str):
                    city = city_data.strip() if city_data.strip() else 'Nieznane miasto'
                else:
                    city = 'Nieznane miasto'
                
                name = station.get('stationName', 'Nieznana stacja')
                display_text = f"{city} - {name}"
                self.stations_listbox.insert(tk.END, display_text)

            # Update last import time for stations
            self.update_last_import_time(
                "Pobieranie stacji z API",
                f"{len(stations)} stacji"
            )

            self.status_var.set(f"Pobrano {len(stations)} stacji z API")
        
        except Exception as e:
            self.status_var.set(f"Błąd pobierania stacji: {e}")
            messagebox.showerror("Błąd", f"Nie udało się pobrać stacji: {e}")
            print(f"Error details: {e}")
            import traceback
            traceback.print_exc()  # This will show the full traceback

    def show_air_quality_index(self):
        """Display air quality index for selected station."""
        if not self.current_station:
            messagebox.showwarning("Ostrzeżenie", "Proszę wybrać stację.")
            return
            
        self.status_var.set("Pobieranie indeksu jakości powietrza...")
        self.root.update()
        
        try:
            index_data = self.api.get_air_quality_index(self.current_station['id'])
            if index_data:
                index_level = self.analyzer.get_air_quality_index_level(index_data)
                
                if index_level:
                    messagebox.showinfo(
                        "Indeks Jakości Powietrza",
                        f"Stacja: {self.current_station['stationName']}\n"
                        f"Indeks: {index_level}"
                    )
                else:
                    messagebox.showinfo("Info", "Brak danych o indeksie jakości powietrza dla wybranej stacji.")
                    
                self.status_var.set("Pobrano indeks jakości powietrza")
            else:
                self.status_var.set("Brak danych o indeksie")
                
        except Exception as e:
            self.status_var.set(f"Błąd pobierania indeksu: {e}")
            messagebox.showerror("Błąd", f"Nie udało się pobrać indeksu: {e}")

    def save_current_data(self):
        """Save current measurements to file."""
        if not self.current_measurements:
            messagebox.showwarning("Ostrzeżenie", "Brak danych do zapisania.")
            return
            
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("Text files", "*.txt"), ("All files", "*.*")]
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("Data,Stężenie [μg/m³]\n")
                    for measurement in self.current_measurements:
                        date_str = measurement['date'].strftime('%Y-%m-%d %H:%M:%S')
                        f.write(f"{date_str},{measurement['value']}\n")
                
                self.status_var.set(f"Zapisano dane do: {filename}")
                messagebox.showinfo("Sukces", f"Dane zapisano do pliku: {filename}")
                self.add_to_import_history("Zapisywanie danych", f"Plik: {filename}")
                
        except Exception as e:
            self.status_var.set(f"Błąd zapisu: {e}")
            messagebox.showerror("Błąd", f"Nie udało się zapisać danych: {e}")

    def show_about(self):
        """Display about information with API limitations."""
        about_text = (
            "Monitor Jakości Powietrza w Polsce\n"
            "Wersja 1.0\n\n"
            "Aplikacja do monitorowania jakości powietrza\n"
            "w oparciu o dane z GIOŚ API.\n\n"
            "Funkcje:\n"
            "- Przeglądanie stacji pomiarowych\n"
            "- Pobieranie danych pomiarowych\n"
            "- Analiza statystyczna\n"
            "- Wizualizacja danych na wykresach\n"
            "- Indeks jakości powietrza\n"
            "- Historia importów danych\n"
            "- Testowanie dostępności danych\n\n"
            "⚠️  OGRANICZENIA:\n"
            "• Publiczne API GIOŚ zwraca tylko dane z ostatnich godzin/dni\n"
            "• Pełne dane historyczne nie są dostępne\n"
            "• Aplikacja pokazuje rzeczywiste możliwości API"
        )
        messagebox.showinfo("O programie", about_text)

    def on_closing(self):
        """Handle application closing."""
        try:
            self.db.close()
        except Exception:
            pass
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = AirQualityApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()