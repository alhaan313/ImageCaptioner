from dotenv import load_dotenv
import os

load_dotenv()
token_key = os.getenv('TOKEN_KEY')
cerebras_api_key = os.getenv('CEREBRAS_API_KEY')