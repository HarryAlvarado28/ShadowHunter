package main

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"os"
	"sort"
	"strings"
)

func main() {
	fmt.Println("\n[🕵️] Módulo OSINT activo")

	fmt.Print("[+] Ingresa el dominio objetivo (ejemplo.com): ")
	var target string
	fmt.Scanln(&target)

	if target == "" {
		fmt.Println("❌ Dominio no proporcionado.")
		return
	}

	url := fmt.Sprintf("https://crt.sh/?q=%%25.%s&output=json", target)
	resp, err := http.Get(url)
	if err != nil {
		fmt.Printf("❌ Error al consultar crt.sh: %v\n", err)
		return
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		fmt.Printf("❌ Error HTTP: Código %d\n", resp.StatusCode)
		return
	}

	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		fmt.Printf("❌ Error al leer respuesta: %v\n", err)
		return
	}

	var data []map[string]interface{}
	err = json.Unmarshal(body, &data)
	if err != nil {
		fmt.Printf("❌ Error al parsear JSON: %v\n", err)
		return
	}

	subdomains := make(map[string]bool)

	for _, entry := range data {
		if nameValue, ok := entry["name_value"].(string); ok {
			names := strings.Split(nameValue, "\n")
			for _, name := range names {
				subdomains[name] = true
			}
		}
	}

	if len(subdomains) == 0 {
		fmt.Println("⚠️ No se encontraron subdominios.")
		return
	}

	fmt.Printf("[+] Subdominios encontrados para %s:\n", target)
	
	// Ordenar alfabéticamente antes de imprimir
	keys := make([]string, 0, len(subdomains))
	for sub := range subdomains {
		keys = append(keys, sub)
	}
	sort.Strings(keys)

	for _, sub := range keys {
		fmt.Printf(" - %s\n", sub)
	}

	fmt.Println("\n✅ Finalizado módulo OSINT.\n")
}
