package main

import (
	"flag"
	"fmt"
	"net"
	"sync"
	"time"
)

func scanPort(wg *sync.WaitGroup, protocol, hostname string, port int) {
	defer wg.Done()
	address := fmt.Sprintf("%s:%d", hostname, port)
	conn, err := net.DialTimeout(protocol, address, 500*time.Millisecond)

	if err != nil {
		return
	}
	defer conn.Close()
	fmt.Printf("[+] Puerto abierto: %d\n", port)
}

func main() {
	var (
		target    string
		startPort int
		endPort   int
	)

	flag.StringVar(&target, "host", "localhost", "Host o IP objetivo")
	flag.IntVar(&startPort, "start", 1, "Puerto inicial")
	flag.IntVar(&endPort, "end", 1024, "Puerto final")
	flag.Parse()

	fmt.Printf("Escaneando %s desde el puerto %d hasta el %d...\n", target, startPort, endPort)

	var wg sync.WaitGroup
	for port := startPort; port <= endPort; port++ {
		wg.Add(1)
		go scanPort(&wg, "tcp", target, port)
	}
	wg.Wait()
}
