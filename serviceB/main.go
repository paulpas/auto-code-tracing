// serviceB/main.go
package main

import (
    "encoding/base64"
    "encoding/json"
    "fmt"
    "log"
    "net/http"
)

type WorkRequest struct {
    Cipher string `json:"cipher"`
}
type WorkResponse struct {
    Result string `json:"result"`
}

/* ---------- 1️⃣ transform (plain data) ---------- */
func transform(payload string) string {
    return fmt.Sprintf("transformed[%s]", payload)
}

/* ---------- 2️⃣ store (no‑op) ---------- */
func store(data string) error {
    // In a real system you would write to a DB.
    return nil
}

/* ---------- 3️⃣ respond ---------- */
func respond(w http.ResponseWriter, data string) {
    resp := WorkResponse{Result: data}
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(resp)
}

/* ---------- HTTP entry point ---------- */
func workHandler(w http.ResponseWriter, r *http.Request) {
    var req WorkRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, "bad json", http.StatusBadRequest)
        return
    }
    // Decode base64 ciphertext
    cipherBytes, err := base64.StdEncoding.DecodeString(req.Cipher)
    if err != nil {
        http.Error(w, "base64 decode error: "+err.Error(), http.StatusBadRequest)
        return
    }
    plainBytes, err := decryptAESGCM(cipherBytes)
    if err != nil {
        http.Error(w, "decryption error: "+err.Error(), http.StatusBadRequest)
        return
    }
    plain := string(plainBytes)

    // Run original business logic on the plain payload
    t := transform(plain)
    if err := store(t); err != nil {
        http.Error(w, "store error: "+err.Error(), http.StatusInternalServerError)
        return
    }
    respond(w, t)
}

/* ---------- main ---------- */
func main() {
    http.HandleFunc("/work", workHandler)
    log.Println("serviceB listening on :8082")
    log.Fatal(http.ListenAndServe(":8082", nil))
}
