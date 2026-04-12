import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Reads the .env file and loads SUPABASE_URL and SUPABASE_KEY into memory
load_dotenv()

# os.getenv("SUPABASE_URL") means: go find the variable named SUPABASE_URL in the .env file
# This way the real values never appear in your code — only the variable names do
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Create the Supabase client using those values
# This is the object every other file imports to talk to the database
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
