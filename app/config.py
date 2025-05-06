from dotenv import load_dotenv
import os

load_dotenv()

# API Keys
token_key = os.getenv('TOKEN_KEY')
cerebras_api_key = os.getenv('CEREBRAS_API_KEY')
huggingface_token = os.getenv('HUGGINGFACE_TOKEN')
phosus_api_key = os.getenv('PHOSUS_API_KEY')
phosus_key_id = int(os.getenv('PHOSUS_KEY_ID'))