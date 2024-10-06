import os
import logging
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
API_URL = os.getenv('API_URL', 'http://127.0.0.1:5000/chat')
TIMEOUT = int(os.getenv('TIMEOUT', 30))

def query_chat_api(user_question: str):
    payload = {'userquestion': user_question}
    try:
        response = requests.post(API_URL, json=payload, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error querying the chat API: {e}")
        return {"error": str(e)}

def main():
    logger.info("Starting the Echo chat client...")

    while True:
        user_question = input("Please enter your query (or 'exit' to quit): ")
        if user_question.lower() == 'exit':
            logger.info("Exiting chat...")
            break

        response = query_chat_api(user_question)
        if "error" in response:
            print(f"Error: {response['error']}")
        else:
            print("Chat Assistant:", response.get('response', 'No response received'))

if __name__ == "__main__":
    main()
