package main

import (
	"crypto/sha256"
	"fmt"
	"os"
	"path/filepath"
	"testing"
)

func TestAnalyze(t *testing.T) {
	dir := t.TempDir()
	if err := os.WriteFile(filepath.Join(dir, "evidence.txt"), []byte("hello"), 0600); err != nil {
		t.Fatal(err)
	}
	rep, err := analyze(dir, 2)
	if err != nil {
		t.Fatal(err)
	}
	if len(rep.Files) != 1 {
		t.Fatalf("want 1 file, got %d", len(rep.Files))
	}
	want := fmt.Sprintf("%x", sha256.Sum256([]byte("hello")))
	if rep.Files[0].SHA256 != want {
		t.Fatalf("digest mismatch: %s", rep.Files[0].SHA256)
	}
}
