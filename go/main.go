package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
)

const BRAIN_URL = "http://localhost:5000"

type ChatRequest struct {
	Prompt string `json:"prompt"`
	Model  string `json:"model,omitempty"`
}

type ChatResponse struct {
	Reply string `json:"reply"`
}

type HealthResponse struct {
	Status string `json:"status"`
}

func askReverie(prompt string, model string) (string, error) {
	payload := ChatRequest{Prompt: prompt, Model: model}
	data, err := json.Marshal(payload)
	if err != nil {
		return "", err
	}
	resp, err := http.Post(
		BRAIN_URL+"/ask",
		"application/json",
		bytes.NewBuffer(data),
	)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", err
	}
	var result ChatResponse
	json.Unmarshal(body, &result)
	return result.Reply, nil
}

func corsMiddleware(next http.HandlerFunc) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Content-Type")
		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}
		next(w, r)
	}
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(HealthResponse{Status: "Reverie Go server online"})
}

func chatHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	var req ChatRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Bad request", http.StatusBadRequest)
		return
	}
	if req.Prompt == "" {
		http.Error(w, "No prompt", http.StatusBadRequest)
		return
	}
	reply, err := askReverie(req.Prompt, req.Model)
	if err != nil {
		log.Printf("Brain error: %v", err)
		json.NewEncoder(w).Encode(ChatResponse{Reply: "Reverie is unreachable"})
		return
	}
	json.NewEncoder(w).Encode(ChatResponse{Reply: reply})
}

func resetHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	http.Post(BRAIN_URL+"/reset", "application/json", nil)
	json.NewEncoder(w).Encode(map[string]string{"status": "Memory cleared"})
}

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	http.HandleFunc("/health", corsMiddleware(healthHandler))
	http.HandleFunc("/chat", corsMiddleware(chatHandler))
	http.HandleFunc("/reset", corsMiddleware(resetHandler))
	fmt.Printf("DEATH.AI Go server running on :%s\n", port)
	log.Fatal(http.ListenAndServe(":"+port, nil))
}
