package main

import (
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
	fmt.Printf("[+] Puerto encontrado: %d\n", port)
}

func main() {
	var wg sync.WaitGroup
	target := "scanme.nmap.org"
	fmt.Printf("Escaneando puertos en %s\n", target)

	for port := 1; port <= 1024; port++ {
		wg.Add(1)
		go scanPort(&wg, "tcp", target, port)
	}

	wg.Wait()
}
