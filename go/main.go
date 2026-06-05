package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"
)

var (
	brainURL   = getenv("BRAIN_URL", "http://localhost:5000")
	httpClient = &http.Client{Timeout: 130 * time.Second}
)

type ChatRequest struct {
	Prompt        string `json:"prompt"`
	Model         string `json:"model,omitempty"`
	ClientContext string `json:"client_context,omitempty"`
}

type ChatResponse struct {
	Reply string `json:"reply"`
}

type HealthResponse struct {
	Status string `json:"status"`
}

func getenv(key string, fallback string) string {
	value := strings.TrimSpace(os.Getenv(key))
	if value == "" {
		return fallback
	}
	return value
}

func writeJSON(w http.ResponseWriter, status int, payload any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	if err := json.NewEncoder(w).Encode(payload); err != nil {
		log.Printf("JSON encode error: %v", err)
	}
}

func proxyJSON(w http.ResponseWriter, method string, path string, body io.Reader) {
	req, err := http.NewRequest(method, brainURL+path, body)
	if err != nil {
		writeJSON(w, http.StatusInternalServerError, map[string]string{"error": "Proxy request failed"})
		return
	}
	if body != nil {
		req.Header.Set("Content-Type", "application/json")
	}
	resp, err := httpClient.Do(req)
	if err != nil {
		log.Printf("Brain proxy error %s %s: %v", method, path, err)
		writeJSON(w, http.StatusBadGateway, map[string]string{"error": "Reverie brain is unreachable"})
		return
	}
	defer resp.Body.Close()
	w.Header().Set("Content-Type", resp.Header.Get("Content-Type"))
	w.WriteHeader(resp.StatusCode)
	if _, err := io.Copy(w, resp.Body); err != nil {
		log.Printf("Proxy response copy error: %v", err)
	}
}

func askReverie(prompt string, model string, clientContext string) (string, error) {
	payload := ChatRequest{Prompt: prompt, Model: model, ClientContext: clientContext}
	data, err := json.Marshal(payload)
	if err != nil {
		return "", err
	}
	resp, err := httpClient.Post(brainURL+"/ask", "application/json", bytes.NewBuffer(data))
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", err
	}
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return "", fmt.Errorf("brain returned %d: %s", resp.StatusCode, string(body))
	}
	var result ChatResponse
	if err := json.Unmarshal(body, &result); err != nil {
		return "", err
	}
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

func indexHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	path, err := chatHTMLPath()
	if err != nil {
		log.Printf("chat.html not found: %v", err)
		http.Error(w, "chat.html not found", http.StatusInternalServerError)
		return
	}
	http.ServeFile(w, r, path)
}

func assetsHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	path, err := assetsPath()
	if err != nil {
		http.NotFound(w, r)
		return
	}
	http.StripPrefix("/assets/", http.FileServer(http.Dir(path))).ServeHTTP(w, r)
}

func reveAnimationsHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	path, err := reveAnimationsPath()
	if err != nil {
		http.NotFound(w, r)
		return
	}
	http.StripPrefix("/reve-animations/", http.FileServer(http.Dir(path))).ServeHTTP(w, r)
}

func chatHTMLPath() (string, error) {
	if configured := strings.TrimSpace(os.Getenv("CHAT_HTML_PATH")); configured != "" {
		if _, err := os.Stat(configured); err == nil {
			return configured, nil
		}
	}
	candidates := []string{
		filepath.Join("..", "python", "core", "chat.html"),
		filepath.Join("python", "core", "chat.html"),
	}
	for _, candidate := range candidates {
		absolute, err := filepath.Abs(candidate)
		if err != nil {
			continue
		}
		if _, err := os.Stat(absolute); err == nil {
			return absolute, nil
		}
	}
	return "", fmt.Errorf("no chat.html candidate exists")
}

func reveAnimationsPath() (string, error) {
	if configured := strings.TrimSpace(os.Getenv("REVE_ANIMATIONS_PATH")); configured != "" {
		if info, err := os.Stat(configured); err == nil && info.IsDir() {
			return configured, nil
		}
	}
	candidates := []string{
		filepath.Join("..", "reve animations"),
		filepath.Join("reve animations"),
	}
	for _, candidate := range candidates {
		absolute, err := filepath.Abs(candidate)
		if err != nil {
			continue
		}
		if info, err := os.Stat(absolute); err == nil && info.IsDir() {
			return absolute, nil
		}
	}
	return "", fmt.Errorf("no reve animations directory exists")
}

func assetsPath() (string, error) {
	if configured := strings.TrimSpace(os.Getenv("CHAT_ASSETS_PATH")); configured != "" {
		if info, err := os.Stat(configured); err == nil && info.IsDir() {
			return configured, nil
		}
	}
	candidates := []string{
		filepath.Join("..", "python", "core", "assets"),
		filepath.Join("python", "core", "assets"),
	}
	for _, candidate := range candidates {
		absolute, err := filepath.Abs(candidate)
		if err != nil {
			continue
		}
		if info, err := os.Stat(absolute); err == nil && info.IsDir() {
			return absolute, nil
		}
	}
	return "", fmt.Errorf("no assets directory exists")
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodGet {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	writeJSON(w, http.StatusOK, HealthResponse{Status: "Reverie Go server online"})
}

func chatHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	var req ChatRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "Bad request"})
		return
	}
	req.Prompt = strings.TrimSpace(req.Prompt)
	req.Model = strings.TrimSpace(req.Model)
	req.ClientContext = strings.TrimSpace(req.ClientContext)
	if req.Prompt == "" {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "No prompt"})
		return
	}
	reply, err := askReverie(req.Prompt, req.Model, req.ClientContext)
	if err != nil {
		log.Printf("Brain error: %v", err)
		writeJSON(w, http.StatusBadGateway, ChatResponse{Reply: "Reverie is unreachable"})
		return
	}
	writeJSON(w, http.StatusOK, ChatResponse{Reply: reply})
}

func historyHandler(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path == "/history" {
		if r.Method != http.MethodGet {
			http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
			return
		}
		proxyJSON(w, http.MethodGet, "/history", nil)
		return
	}
	if !strings.HasPrefix(r.URL.Path, "/history/") {
		http.NotFound(w, r)
		return
	}
	if r.Method != http.MethodDelete {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	id := strings.TrimPrefix(r.URL.Path, "/history/")
	if id == "" || strings.Contains(id, "/") {
		writeJSON(w, http.StatusBadRequest, map[string]string{"error": "Invalid history id"})
		return
	}
	for _, char := range id {
		if char < '0' || char > '9' {
			writeJSON(w, http.StatusBadRequest, map[string]string{"error": "Invalid history id"})
			return
		}
	}
	proxyJSON(w, http.MethodDelete, "/history/"+id, nil)
}

func resetHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
		return
	}
	proxyJSON(w, http.MethodPost, "/reset", nil)
}

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	http.HandleFunc("/", corsMiddleware(indexHandler))
	http.HandleFunc("/assets/", corsMiddleware(assetsHandler))
	http.HandleFunc("/reve-animations/", corsMiddleware(reveAnimationsHandler))
	http.HandleFunc("/health", corsMiddleware(healthHandler))
	http.HandleFunc("/ask", corsMiddleware(chatHandler))
	http.HandleFunc("/chat", corsMiddleware(chatHandler))
	http.HandleFunc("/history", corsMiddleware(historyHandler))
	http.HandleFunc("/history/", corsMiddleware(historyHandler))
	http.HandleFunc("/reset", corsMiddleware(resetHandler))
	fmt.Printf("DEATH.AI Go server running on :%s\n", port)
	log.Fatal(http.ListenAndServe(":"+port, nil))
}
