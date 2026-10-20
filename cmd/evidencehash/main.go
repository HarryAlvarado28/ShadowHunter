// Command evidencehash hashes local regular files using a bounded worker pool.
package main

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"runtime"
	"sort"
	"sync"
)

const maxFiles = 256
const maxEntries = 4096
const maxFileBytes = 16 << 20

type record struct {
	Path   string `json:"path"`
	SHA256 string `json:"sha256"`
	Size   int64  `json:"size"`
	Error  string `json:"error,omitempty"`
}

type report struct {
	Engine    string   `json:"engine"`
	Directory string   `json:"directory"`
	Files     []record `json:"files"`
	Skipped   int      `json:"skipped"`
}

func hashFile(root, rel string) record {
	path := filepath.Join(root, rel)
	info, err := os.Lstat(path)
	if err != nil {
		return record{Path: rel, Error: err.Error()}
	}
	if !info.Mode().IsRegular() || info.Size() > maxFileBytes {
		return record{Path: rel, Error: "not a supported regular file (max 16 MiB)"}
	}
	f, err := os.Open(path)
	if err != nil {
		return record{Path: rel, Error: err.Error()}
	}
	defer f.Close()
	sum := sha256.New()
	size, err := io.Copy(sum, io.LimitReader(f, maxFileBytes+1))
	if err != nil {
		return record{Path: rel, Error: err.Error()}
	}
	if size > maxFileBytes {
		return record{Path: rel, Error: "file grew past size limit"}
	}
	return record{Path: rel, Size: size, SHA256: hex.EncodeToString(sum.Sum(nil))}
}

func analyze(dir string, workers int) (report, error) {
	if workers < 1 || workers > 4 {
		return report{}, errors.New("workers must be in range 1..4")
	}
	abs, err := filepath.Abs(dir)
	if err != nil {
		return report{}, err
	}
	info, err := os.Lstat(abs)
	if err != nil {
		return report{}, err
	}
	if !info.IsDir() || info.Mode()&os.ModeSymlink != 0 {
		return report{}, errors.New("target must be a directory, not a symlink")
	}
	rep := report{Engine: "go", Directory: abs, Files: []record{}}
	paths := make([]string, 0)
	entries := 0
	err = filepath.WalkDir(abs, func(path string, d os.DirEntry, e error) error {
		if e != nil {
			return e
		}
		entries++
		if entries > maxEntries {
			return errors.New("directory exceeds 4096 entries")
		}
		if path == abs {
			return nil
		}
		if d.Type()&os.ModeSymlink != 0 {
			rep.Skipped++
			return nil
		}
		if d.IsDir() {
			return nil
		}
		inf, e := d.Info()
		if e != nil {
			return e
		}
		if !inf.Mode().IsRegular() || inf.Size() > maxFileBytes {
			rep.Skipped++
			return nil
		}
		if len(paths) >= maxFiles {
			return errors.New("directory exceeds 256 eligible files")
		}
		rel, e := filepath.Rel(abs, path)
		if e != nil {
			return e
		}
		paths = append(paths, rel)
		return nil
	})
	if err != nil {
		return report{}, err
	}
	jobs := make(chan string)
	results := make(chan record, len(paths))
	var wg sync.WaitGroup
	for i := 0; i < workers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for rel := range jobs {
				results <- hashFile(abs, rel)
			}
		}()
	}
	for _, path := range paths {
		jobs <- path
	}
	close(jobs)
	wg.Wait()
	close(results)
	for item := range results {
		rep.Files = append(rep.Files, item)
	}
	sort.Slice(rep.Files, func(i, j int) bool { return rep.Files[i].Path < rep.Files[j].Path })
	return rep, nil
}

func main() {
	dir := flag.String("dir", "", "Local evidence directory")
	workers := flag.Int("workers", runtime.NumCPU(), "Bounded concurrency 1..4")
	flag.Parse()
	if *dir == "" {
		fmt.Fprintln(os.Stderr, "usage: shadowhunter-worker --dir DIRECTORY [--workers 1..4]")
		os.Exit(2)
	}
	if *workers > 4 {
		*workers = 4
	}
	rep, err := analyze(*dir, *workers)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	if err := json.NewEncoder(os.Stdout).Encode(rep); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
