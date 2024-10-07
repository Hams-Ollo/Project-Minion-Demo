import os
import logging
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
# This allows you to store configuration data (like API URLs and timeouts) in a separate file,
# making it easy to change without altering the codebase.
load_dotenv()

# Configure logging for the client script
# Logging is important for tracking the flow of execution and capturing errors for debugging purposes.
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
# API_URL and TIMEOUT are constants used to configure the API client.
# API_URL is the endpoint that the script will communicate with.
# TIMEOUT defines how long the script should wait for a response before timing out.
API_URL = os.getenv('API_URL', 'http://127.0.0.1:5000/chat')  # Default to local server if not specified
TIMEOUT = int(os.getenv('TIMEOUT', 30))  # Set a timeout of 30 seconds by default

# Function to query the chat API
# This function sends the user's question to the chat API and waits for a response.
def query_chat_api(user_question: str):
    # Prepare the payload to be sent to the API
    payload = {'userquestion': user_question}
    
    try:
        # Send a POST request to the API
        # We use requests.post() to interact with the API and pass the question as JSON data.
        response = requests.post(API_URL, json=payload, timeout=TIMEOUT)

        # If the response contains an error status code (like 4xx or 5xx), raise an exception
        response.raise_for_status()

        # Return the response from the API in JSON format
        return response.json()
    
    # Handle any errors that occur during the request
    # This includes connectivity issues, server errors, or timeouts.
    except requests.RequestException as e:
        # Log the error details for troubleshooting
        logger.error(f"Error querying the chat API: {e}")

        # Return an error message to the caller function
        return {"error": str(e)}

# Function to add contextual emojis based on agent response
def add_emojis_to_response(response: str) -> str:
    # Determine the appropriate emoji based on the agent type in the response
    if "cat" in response.lower():
        return f"🐱 Cat Minion: {response}"
    elif "dog" in response.lower():
        return f"🐶 Dog Minion: {response}"
    elif "monkey" in response.lower():
        return f"🐵 Monkey Minion: {response}"
    elif "receptionist" in response.lower():
        return f"📞 Receptionist Minion: {response}"
    else:
        return f"🤖 Orchestrator Minion: {response}"  # Default emoji for general or unspecified responses

# Main function to run the client application
# This function provides an interactive loop where the user can repeatedly ask questions.
def main():
    # Log that the chat client has started
    logger.info("Starting the Echo chat client...")

    # Infinite loop to keep the chat client running until the user decides to quit
    while True:
        # Prompt the user for input
        user_question = input("Please enter your query (or 'exit' to quit): ")
        
        # Check if the user wants to exit the chat
        if user_question.lower() == 'exit':
            # Log that the user has decided to exit and break the loop
            logger.info("Exiting chat...")
            break

        # Query the chat API with the user's input
        response = query_chat_api(user_question)

        # Check if the response contains an error
        if "error" in response:
            # Print the error message if something went wrong
            print(f"❌ Error: {response['error']}")
        else:
            # Print the response from the Chat Assistant, adding contextual emojis
            raw_response = response.get('response', 'No response received')
            emoji_response = add_emojis_to_response(raw_response)
            print(emoji_response)

# Entry point for the script
# When this script is run directly, it calls the main function.
if __name__ == "__main__":
    main()
