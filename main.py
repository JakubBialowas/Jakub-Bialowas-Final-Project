"""
Main module for the Air Quality Monitoring Application.
This is the entry point of the application.
"""

import tkinter as tk
import sys
import importlib
import subprocess
import os

REQUIRED_PACKAGES = [
    "requests>=2.28.0",
    "pandas>=1.5.0",
    "matplotlib>=3.6.0",
    "geopy>=2.3.0",
    "Pillow>=9.3.0",
    "tkcalendar>=1.6.1",
    "scipy>=1.15"
]

def create_requirements_file():
    """Create requirements.txt file."""
    with open('requirements.txt', 'w') as f:
        for package in REQUIRED_PACKAGES:
            f.write(package + '\n')
    print("✓ Created requirements.txt file")

def check_dependencies():
    """Check if all required dependencies are installed."""
    missing_packages = []
    
    for package in REQUIRED_PACKAGES:
        package_name = package.split('>=')[0] if '>=' in package else package.split('==')[0]
        
        try:
            if package_name == "Pillow":
                importlib.import_module("PIL")
            else:
                importlib.import_module(package_name)
        except ImportError:
            missing_packages.append(package_name)
    
    return missing_packages

def install_dependencies():
    """Install missing dependencies."""
    try:
        print("Installing missing dependencies...")
        # Create requirements file first
        create_requirements_file()
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        return True
    except subprocess.CalledProcessError:
        return False

def setup_environment():
    """Setup the application environment."""
    print("=" * 50)
    print("Air Quality Monitoring Application Setup")
    print("=" * 50)
    
    # Check for missing dependencies
    missing = check_dependencies()
    
    if missing:
        print(f"Missing dependencies: {', '.join(missing)}")
        response = input("Installing automatically...")
        
        if missing:
            if install_dependencies():
                print("Dependencies installed successfully! Restarting application...")
                subprocess.call([sys.executable] + sys.argv)
                sys.exit(0)
            else:
                print("Failed to install dependencies. Please run: pip install -r requirements.txt")
    print("✓ All dependencies are installed")
    return True

def main():
    """
    Main function to run the Tkinter application.
    """
    # Setup environment and check dependencies
    if not setup_environment():
        print("Application cannot start due to missing dependencies.")
        return

    # Try importing the GUI app with detailed error info
    try:
        print("Attempting to import AirQualityApp...")
        from air_quality.interface import AirQualityApp
        print("✓ Successfully imported AirQualityApp")
    except ImportError as e:
        print(f"❌ Error importing AirQualityApp: {e}")
        print("Detailed error traceback:")
        import traceback
        traceback.print_exc()
        
        # Try to diagnose the issue
        try:
            print("\nChecking if database module can be imported...")
            from air_quality import database
            print("✓ Database module imported successfully")
            
            print("Checking if AirQualityDatabase class exists...")
            if hasattr(database, 'AirQualityDatabase'):
                print("✓ AirQualityDatabase class found")
            else:
                print("❌ AirQualityDatabase class NOT found in database module")
                print("Available attributes in database module:")
                for attr in dir(database):
                    if not attr.startswith('_'):
                        print(f"  - {attr}")
                
        except ImportError as db_error:
            print(f"❌ Error importing database module: {db_error}")
            import traceback
            traceback.print_exc()
        
        AirQualityApp = None

    # Run the GUI if possible
    if AirQualityApp:
        try:
            root = tk.Tk()
            app = AirQualityApp(root)
            
            # Set window icon and title
            root.title("Monitor Jakości Powietrza w Polsce - GIOŚ")
            
            # Center the window on screen
            window_width = 1000
            window_height = 700
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            center_x = int(screen_width/2 - window_width/2)
            center_y = int(screen_height/2 - window_height/2)
            root.geometry(f'{window_width}x{window_height}+{center_x}+{center_y}')
            
            # Set minimum window size
            root.minsize(800, 600)
            
            # Handle window closing
            root.protocol("WM_DELETE_WINDOW", app.on_closing)
            
            # Start the application
            root.mainloop()
            
        except Exception as e:
            print(f"Error running the GUI application: {e}")
            import traceback
            traceback.print_exc()
            AirQualityApp = None

    # Fallback console message if GUI cannot start
    if not AirQualityApp:
        print("\n" + "="*50)
        print("AIR QUALITY MONITORING APPLICATION")
        print("="*50)
        print("The graphical interface could not be started.")
        print("Please check if all dependencies are installed and AirQualityDatabase exists in air_quality/database.py")
        print("Dependencies:")
        print("pip install requests pandas matplotlib geopy Pillow tkcalendar")
        print("="*50)

if __name__ == "__main__":
    main()