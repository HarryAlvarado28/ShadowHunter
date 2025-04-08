import requests
from bs4 import BeautifulSoup
import sys

def basic_osint(target_url):
    try:
        response = requests.get(target_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        print(f"Título del sitio: {soup.title.string}")
        print(f"Servidor: {response.headers.get('Server', 'No disponible')}")
        print(f"Estado HTTP: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error al acceder: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python osint.py <url>")
    else:
        basic_osint(sys.argv[1])
