// Optional OSINT prototype. This binary is not required by the Python workbench.
package main

import (
    "encoding/json"
    "fmt"
    "io"
    "net/http"
    "net/url"
    "os"
    "regexp"
    "sort"
    "strings"
    "time"
)

const maxResponse = 1_048_576
var domainPattern = regexp.MustCompile("(?i)^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\\.)+[a-z][a-z0-9-]{1,62}$")

type certRecord struct {
    NameValue string `json:"name_value"`
}

func main() {
    fmt.Println("🕵️ ShadowHunter / optional CT lookup (Go)")
    fmt.Print("Authorized research domain (e.g. example.org): ")
    var input string
    if _, err := fmt.Scanln(&input); err != nil {
        fmt.Fprintln(os.Stderr, "Unable to read domain:", err)
        os.Exit(1)
    }
    target := strings.TrimSuffix(strings.ToLower(strings.TrimSpace(input)), ".")
    if len(target) > 253 || !domainPattern.MatchString(target) {
        fmt.Fprintln(os.Stderr, "Invalid domain; supply a DNS name without scheme or path.")
        os.Exit(2)
    }

    u := "https://crt.sh/?" + url.Values{
        "q": {"%." + target}, "output": {"json"},
    }.Encode()
    client := &http.Client{Timeout: 10 * time.Second}
    req, err := http.NewRequest(http.MethodGet, u, nil)
    if err != nil {
        fmt.Fprintln(os.Stderr, err)
        os.Exit(1)
    }
    req.Header.Set("User-Agent", "ShadowHunter/0.2 (public CT research)")
    resp, err := client.Do(req)
    if err != nil {
        fmt.Fprintln(os.Stderr, "CT request failed:", err)
        os.Exit(1)
    }
    defer resp.Body.Close()
    if resp.StatusCode != http.StatusOK {
        fmt.Fprintln(os.Stderr, "Unexpected CT response status:", resp.StatusCode)
        os.Exit(1)
    }
    body, err := io.ReadAll(io.LimitReader(resp.Body, maxResponse+1))
    if err != nil || len(body) > maxResponse {
        fmt.Fprintln(os.Stderr, "CT response unreadable or exceeds 1 MiB.")
        os.Exit(1)
    }
    var data []certRecord
    if err := json.Unmarshal(body, &data); err != nil {
        fmt.Fprintln(os.Stderr, "Invalid CT JSON:", err)
        os.Exit(1)
    }

    result := make(map[string]struct{})
    for _, item := range data {
        for _, raw := range strings.Split(item.NameValue, "
") {
            name := strings.TrimPrefix(strings.ToLower(strings.TrimSpace(raw)), "*.")
            if (name == target || strings.HasSuffix(name, "."+target)) && domainPattern.MatchString(name) {
                result[name] = struct{}{}
            }
        }
    }
    names := make([]string, 0, len(result))
    for name := range result {
        names = append(names, name)
    }
    sort.Strings(names)
    fmt.Printf("Unique public CT names: %d
", len(names))
    for idx, name := range names {
        if idx == 100 {
            fmt.Println("... output limited to 100 names")
            break
        }
        fmt.Println(" -", name)
    }
    fmt.Println("Public certificate names do not prove live hosts or authorization.")
}
