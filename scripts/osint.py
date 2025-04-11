import requests
import sys

def get_subdomains(domain):
    url = f"https://crt.sh/?q=%25.{domain}&output=json"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"Error al consultar crt.sh: {response.status_code}")
            return

        entries = response.json()
        subdomains = set()
        for entry in entries:
            name = entry.get("name_value")
            if name:
                subdomains.update(name.split("\n"))

        print(f"Subdominios encontrados para {domain}:")
        for sub in sorted(subdomains):
            print(f" - {sub}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python osint.py <dominio>")
    else:
        get_subdomains(sys.argv[1])
