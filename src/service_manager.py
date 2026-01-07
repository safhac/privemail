import logging
import subprocess
import time
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

OLLAMA_URL = "http://127.0.0.1:11434"

def check_ollama_server() -> bool:
    """Probes the Ollama server to see if it's running."""
    try:
        with httpx.Client(timeout=2.0) as client:
            response = client.get(OLLAMA_URL)
            return response.status_code == 200
    except httpx.ConnectError:
        return False
    except Exception as e:
        logging.warning(f"Error checking Ollama server: {e}")
        return False

def start_ollama_service():
    """Starts the 'ollama serve' command as a background process safely."""
    if check_ollama_server():
        logging.info("Ollama service is already running.")
        return

    logging.info("Attempting to start Ollama service...")
    try:
        # Start 'ollama serve' silently
        subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        # Wait up to 5 seconds for it to spin up
        for i in range(5):
            time.sleep(1)
            if check_ollama_server():
                logging.info("Ollama service started successfully.")
                return
        
        logging.warning("Ollama service started but did not respond to ping within 5 seconds.")

    except FileNotFoundError:
        logging.error("CRITICAL: 'ollama' command not found. Is it installed?")
        # We do NOT raise error here, allowing the app to boot so UI can show the error.
    except Exception as e:
        logging.error(f"An error occurred while starting Ollama service: {e}")

def auto_start_services():
    """Main entry point to check and start required services."""
    logging.info("Checking external services...")
    start_ollama_service()