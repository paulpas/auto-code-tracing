// crypto_common.go
package main

import (
    "crypto/aes"
    "crypto/cipher"
    "crypto/rand"
    "io"
)

// 32‑byte (256‑bit) symmetric key – **DO NOT** ship this in production!
var sharedKey = []byte{
    0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
    0x08, 0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x0e, 0x0f,
    0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17,
    0x18, 0x19, 0x1a, 0x1b, 0x1c, 0x1d, 0x1e, 0x1f,
}

// encryptAESGCM encrypts plaintext with AES‑GCM.
// Returns (nonce || ciphertext) – the nonce is needed for decryption.
func encryptAESGCM(plain []byte) ([]byte, error) {
    block, err := aes.NewCipher(sharedKey)
    if err != nil {
        return nil, err
    }
    aesgcm, err := cipher.NewGCM(block)
    if err != nil {
        return nil, err
    }
    nonce := make([]byte, aesgcm.NonceSize())
    if _, err = io.ReadFull(rand.Reader, nonce); err != nil {
        return nil, err
    }
    ciphertext := aesgcm.Seal(nil, nonce, plain, nil)
    return append(nonce, ciphertext...), nil
}

// decryptAESGCM expects (nonce || ciphertext) as produced by encryptAESGCM.
func decryptAESGCM(data []byte) ([]byte, error) {
    block, err := aes.NewCipher(sharedKey)
    if err != nil {
        return nil, err
    }
    aesgcm, err := cipher.NewGCM(block)
    if err != nil {
        return nil, err
    }
    nonceSize := aesgcm.NonceSize()
    if len(data) < nonceSize {
        return nil, err
    }
    nonce, ciphertext := data[:nonceSize], data[nonceSize:]
    plain, err := aesgcm.Open(nil, nonce, ciphertext, nil)
    if err != nil {
        return nil, err
    }
    return plain, nil
}
