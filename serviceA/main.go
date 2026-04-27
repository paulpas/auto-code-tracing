// serviceA/main.go
package main

import (
    "bytes"
    "encoding/base64"
    "encoding/json"
    "fmt"
    "io"
    "log"
    "net/http"
    "time"
)

type ProcessRequest struct{ Input string `json:"input"` }
type ProcessResponse struct{ Final string `json:"final"` }

/* ---------- 1️⃣ validate ---------- */
func validate(input string) error {
    if input == "" {
        return fmt.Errorf("empty input")
    }
    return nil
}

/* ---------- 2️⃣ enrich ---------- */
func enrich(input string) string {
    return fmt.Sprintf("%s|ts=%d", input, time.Now().Unix())
}

/* ---------- 3️⃣ call serviceB (encrypt + send) ---------- */
func callServiceB(plainPayload string) (string, error) {
    cipherBytes, err := encryptAESGCM([]byte(plainPayload))
    if err != nil {
        return "", fmt.Errorf("encryption failed: %w", err)
    }
    encoded := base64.StdEncoding.EncodeToString(cipherBytes)

    workReq := struct {
        Cipher string `json:"cipher"`
    }{Cipher: encoded}
    body, _ := json.Marshal(workReq)

    resp, err := http.Post("http://localhost:8082/work", "application/json", bytes.NewReader(body))
    if err != nil {
        return "", err
    }
    defer resp.Body.Close()
    b, _ := io.ReadAll(resp.Body)

    var workResp struct {
        Result string `json:"result"`
    }
    if err := json.Unmarshal(b, &workResp); err != nil {
        return "", err
    }
    return workResp.Result, nil
}

/* ---------- 4️⃣ formatResult ---------- */
func formatResult(serviceBResult string) string {
    return fmt.Sprintf("serviceA processed → %s", serviceBResult)
}

/* ---------- HTTP entry point ---------- */
func processHandler(w http.ResponseWriter, r *http.Request) {
    var in ProcessRequest
    if err := json.NewDecoder(r.Body).Decode(&in); err != nil {
        http.Error(w, "bad json", http.StatusBadRequest)
        return
    }
    if err := validate(in.Input); err != nil {
        http.Error(w, "validation error: "+err.Error(), http.StatusBadRequest)
        return
    }
    enriched := enrich(in.Input)

    b2, err := callServiceB(enriched)
    if err != nil {
        http.Error(w, "serviceB call failed: "+err.Error(), http.StatusBadGateway)
        return
    }
    final := formatResult(b2)

    out := ProcessResponse{Final: final}
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(out)
}

/* ---------- main ---------- */
func main() {
    http.HandleFunc("/process", processHandler)
    log.Println("serviceA listening on :8081")
    log.Fatal(http.ListenAndServe(":8081", nil))
}
