import requests

def run():
    print("\n[🕵️] Módulo OSINT activo")
    target = input("[+] Ingresa el dominio objetivo (ejemplo.com): ").strip()

    if not target:
        print("❌ Dominio no proporcionado.")
        return

    print(f"[~] Buscando subdominios públicos usando crt.sh para: {target}\n")

    try:
        url = f"https://crt.sh/?q=%25.{target}&output=json"
        response = requests.get(url, timeout=10)

        if response.status_code != 200:
            print(f"❌ Error al consultar crt.sh: Código {response.status_code}")
            return

        data = response.json()
        subdominios = set()

        for entry in data:
            name_value = entry.get("name_value")
            if name_value:
                subdominios.update(name_value.split("\n"))

        if subdominios:
            print(f"[+] Subdominios encontrados para {target}:")
            for sub in sorted(subdominios):
                print(f" - {sub}")
        else:
            print("⚠️ No se encontraron subdominios.")

    except Exception as e:
        print(f"❌ Error al realizar la consulta: {e}")

    print("\n✅ Finalizado módulo OSINT.\n")
