
package main

import (
	"bufio"
	"bytes"
	"fmt"
	"os"
	"strings"

	"github.com/go-logfmt/logfmt"
)

func main() {
	scanner := bufio.NewScanner(os.Stdin)

	for scanner.Scan() {
		line := scanner.Text()
		decoder := logfmt.NewDecoder(strings.NewReader(line))

		var pairs [][2]string

		for decoder.ScanRecord() {
			for decoder.ScanKeyval() {
				key := string(decoder.Key())
				val := string(decoder.Value())
				pairs = append(pairs, [2]string{key, val})
			}
			if err := decoder.Err(); err != nil {
				fmt.Fprintf(os.Stderr, "error: %v\n", err)
				os.Exit(1)
			}
		}

		var buf bytes.Buffer
		encoder := logfmt.NewEncoder(&buf)
		for _, kv := range pairs {
			_ = encoder.EncodeKeyval(kv[0], kv[1])
		}
		_ = encoder.EndRecord()

		fmt.Print(buf.String())
	}
}
