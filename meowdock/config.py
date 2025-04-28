from dotenv import load_dotenv
import browser_use, logging

load_dotenv()  # Load environment variables from .env file
logging.getLogger('browser_use').setLevel(logging.ERROR)
