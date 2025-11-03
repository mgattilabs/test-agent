#!/usr/bin/env python3
"""Script di test per verificare che il server FastMCP sia configurato correttamente."""

import sys
from pathlib import Path


def check_env_file():
    """Verifica che il file .env esista e contenga le variabili necessarie."""
    print("🔍 Verifica file .env...")

    env_file = Path(".env")
    if not env_file.exists():
        print("  ❌ File .env non trovato")
        print("     Crea un file .env con:")
        print("       GEMINI_API_KEY=your-key")
        print("       AZDO_PERSONAL_ACCESS_TOKEN=your-token")
        print("       AZDO_ORGANIZATION=your-org")
        return False

    content = env_file.read_text()
    required = ["GEMINI_API_KEY", "AZDO_PERSONAL_ACCESS_TOKEN", "AZDO_ORGANIZATION"]
    missing = []

    for var in required:
        if var in content:
            print(f"  ✅ {var}")
        else:
            print(f"  ❌ {var} - NON TROVATA")
            missing.append(var)

    if missing:
        print(f"\n⚠️  Variabili mancanti nel .env: {', '.join(missing)}")
        return False

    print("\n✅ File .env configurato correttamente!\n")
    return True


def check_main_file():
    """Verifica che main.py esista e contenga FastMCP."""
    print("🔍 Verifica main.py...")

    main_file = Path("main.py")
    if not main_file.exists():
        print("  ❌ main.py non trovato")
        return False

    content = main_file.read_text()

    checks = [
        ("from mcp.server.fastmcp import FastMCP", "Import FastMCP"),
        ("mcp = FastMCP", "Istanza FastMCP"),
        ("@mcp.tool()", "Decoratori tool"),
        ("initialize_azdo_handler", "Tool initialize"),
        ("process_azdo_summary", "Tool process_summary"),
    ]

    for check_str, label in checks:
        if check_str in content:
            print(f"  ✅ {label}")
        else:
            print(f"  ⚠️  {label} - NON TROVATO")

    print("\n✅ main.py sembra configurato correttamente!\n")
    return True


def main():
    """Esegue tutti i controlli."""
    print("\n" + "=" * 60)
    print("  Test FastMCP Server - AzdoProjectHandler")
    print("=" * 60 + "\n")

    all_ok = True

    # Check .env
    if not check_env_file():
        all_ok = False

    # Check main.py
    if not check_main_file():
        all_ok = False

    print("=" * 60)
    if all_ok:
        print("✅ TUTTI I CONTROLLI SUPERATI!")
        print("\nPuoi avviare il server con: python main.py")
        print("\nPer configurare Claude Desktop:")
        print("  1. Copia claude_desktop_config.json nella directory di Claude")
        print("  2. Modifica il campo 'cwd' con il percorso assoluto")
        print("  3. Riavvia Claude Desktop")
    else:
        print("❌ ALCUNI CONTROLLI FALLITI")
        print("\nRisolvi i problemi evidenziati sopra e riprova.")
        sys.exit(1)

    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
