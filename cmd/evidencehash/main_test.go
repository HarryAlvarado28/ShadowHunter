package main

import (
    "os"
    "path/filepath"
    "testing"
)

func TestHashFile(t *testing.T) {
    dir := t.TempDir()
    if err := os.WriteFile(filepath.Join(dir, "sample.txt"), []byte("abc"), 0600); err != nil {
        t.Fatal(err)
    }
    got := hashFile(dir, "sample.txt")
    if got.Error != "" || got.Size != 3 || len(got.SHA256) != 64 {
        t.Fatalf("unexpected hash result: %+v", got)
    }
}
