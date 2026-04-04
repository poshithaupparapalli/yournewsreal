import os
from dotenv import load_dotenv 
from supabase import create_client, Client 
load_dotenv() #reads your .env file and loads the two variables into memory

SUPABASE_URL = os.getenv ("https://lnbnksvxiuhtirjzjlkv.supabase.co") #grabs each value by name

SUPABASE_KEY = os.getenv("sb_publishable_W45ix-Q3NifdQ6B0zSNLDQ_UKt7LDPu")

supabase: Client = create_client("https://lnbnksvxiuhtirjzjlkv.supabase.co","sb_publishable_W45ix-Q3NifdQ6B0zSNLDQ_UKt7LDPu" )  #creates the Supabase connection using those credentials
