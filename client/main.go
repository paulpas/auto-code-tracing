// client/main.go
package main

import (
    "bytes"
    "encoding/json"
    "fmt"
    "net/http"
)

type ProcessRequest struct{ Input string `json:"input"` }
type ProcessResponse struct{ Final string `json:"final"` }

func main() {
    req := ProcessRequest{Input: "hello-world"}
    b, _ := json.Marshal(req)

    resp, err := http.Post("http://localhost:8081/process", "application/json", bytes.NewReader(b))
    if err != nil {
        panic(err)
    }
    defer resp.Body.Close()

    var out ProcessResponse
    if err := json.NewDecoder(resp.Body).Decode(&out); err != nil {
        panic(err)
    }
    fmt.Println("Client got:", out.Final)
}
