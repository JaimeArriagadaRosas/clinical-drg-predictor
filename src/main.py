#!/usr/bin/env python3
"""
GRD Prediction - Main Entry Point
"""

import sys
import os
import subprocess

# Ensure we are running from the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(PROJECT_ROOT)

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def pause():
    input("Presiona Enter para continuar...")

def run_chatbot():
    print("\nIniciando Chatbot API...")
    print("Abre tu navegador en http://localhost:5000\n")
    try:
        subprocess.run([sys.executable, "-m", "src.api.app"])
    except KeyboardInterrupt:
        pass
    pause()

def show_history():
    clear_screen()
    print("========================================")
    print("     Historial de Entrenamientos")
    print("========================================\n")
    history_file = os.path.join("models", "training_history.txt")
    if os.path.exists(history_file):
        with open(history_file, "r", encoding="utf-8") as f:
            print(f.read())
    else:
        print("No hay historial disponible todavia.")
        print("Entrena el modelo al menos una vez para generar el historial.")
    print("")
    pause()

def train_default():
    print("\nIniciando entrenamiento con parametros por defecto...")
    print("  n_estimators=50, max_depth=None, sin LightGBM\n")
    try:
        subprocess.run([sys.executable, "src/training/training_main.py", "--n-estimators", "50", "--skip-lgbm"])
    except KeyboardInterrupt:
        pass
    pause()

def train_custom():
    clear_screen()
    print("========================================")
    print("       Parametros de Entrenamiento")
    print("========================================\n")
    
    print("Cantidad de arboles (n_estimators)")
    print("  4GB  RAM: entre 20 y 100")
    print("  8GB  RAM: entre 100 y 200")
    print("  16GB RAM: entre 200 y 400")
    print("  ENTER para usar valor por defecto [50]\n")
    n_est_input = input("  n_estimators [50]: ").strip()
    n_est = "50" if not n_est_input else n_est_input
    
    print("\nProfundidad maxima de cada arbol (max_depth)")
    print("  4GB  RAM: entre 25 y 50")
    print("  8GB  RAM: entre 50 y 80")
    print("  16GB RAM: None (sin limite) o mayor a 80")
    print("  ENTER para usar None (sin limite)\n")
    max_d_input = input("  max_depth [None]: ").strip()
    max_d = "none" if not max_d_input else max_d_input
    
    print("\nEntrenar tambien LightGBM?")
    print("  4GB  RAM: No recomendado")
    print("  8GB+ RAM: Recomendado, suele superar a Random Forest")
    print("  S = Si   N = No\n")
    use_lgbm_input = input("  Usar LightGBM? [N]: ").strip().upper()
    use_lgbm = "N" if not use_lgbm_input else use_lgbm_input
    
    clear_screen()
    print("========================================")
    print("       Resumen de Configuracion")
    print("========================================\n")
    print(f"  n_estimators : {n_est}")
    print(f"  max_depth    : {max_d}")
    print(f"  LightGBM     : {use_lgbm}\n")
    
    confirm = input("Confirmar y entrenar? (S/N): ").strip().upper()
    if confirm != "S":
        print("Entrenamiento cancelado.")
        pause()
        return
        
    print("\nIniciando entrenamiento...\n")
    cmd = [sys.executable, "src/training/training_main.py", "--n-estimators", n_est]
    if max_d.lower() != "none":
        cmd.extend(["--max-depth", max_d])
    if use_lgbm != "S":
        cmd.append("--skip-lgbm")
        
    try:
        subprocess.run(cmd)
    except KeyboardInterrupt:
        pass
    pause()

def training_menu():
    while True:
        clear_screen()
        print("========================================")
        print("     Configuracion de Entrenamiento")
        print("========================================")
        print("\n  Valores por defecto:")
        print("    n_estimators : 50    (cantidad de arboles)")
        print("    max_depth    : None  (profundidad maxima)")
        print("    LightGBM     : No\n")
        print("  1. Entrenar con valores por defecto")
        print("  2. Personalizar parametros")
        print("  3. Volver al menu principal\n")
        
        choice = input("Selecciona una opcion (1-3): ").strip()
        if choice == "1":
            train_default()
            return
        elif choice == "2":
            train_custom()
            return
        elif choice == "3":
            return
        else:
            print("Opcion invalida.")
            pause()

def main():
    while True:
        clear_screen()
        print("========================================")
        print("       GRD Prediction - Main Menu")
        print("========================================")
        print("\n  1. Entrenar modelo")
        print("  2. Iniciar Chatbot")
        print("  3. Ver historial de entrenamientos")
        print("  4. Salir\n")
        
        choice = input("Selecciona una opcion (1-4): ").strip()
        if choice == "1":
            training_menu()
        elif choice == "2":
            run_chatbot()
        elif choice == "3":
            show_history()
        elif choice == "4":
            print("\nHasta luego!")
            break
        else:
            print("Opcion invalida, intenta de nuevo.")
            pause()

if __name__ == "__main__":
    main()