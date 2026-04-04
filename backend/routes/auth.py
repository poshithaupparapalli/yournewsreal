from fastapi import APIRouter, HTTPException                                              
from pydantic import BaseModel                                                            
from typing import List                                                                   
import bcrypt                                                                             
from database.connection import supabase
                                                                                            
  # APIRouter lets us define routes in a separate file from main.py                         
  # Think of it as a mini-app that main.py will plug in                                     
router = APIRouter()                                                                      
                  
  # This class defines the exact shape of JSON we expect from the browser                   
  # Pydantic will automatically reject any request that doesn't match this shape
  # For example if email is missing or sources is not a list, FastAPI rejects it before our 
  # code runs                                                                                 
class OnboardingData(BaseModel):                                                          
      name: str           # must be a string                                                
      email: str          # must be a string
      password: str       # must be a string
      sources: List[str]  # must be a list of strings e.g. ["NYT", "BBC"]                   
      interests: List[str]# must be a list of strings e.g. ["AI", "Finance"]
      niche_entities: str # comma separated string e.g. "Jensen Huang, NVIDIA"              
      reading_time: str                                                                     
      format: str                                                                           
      delivery_time: str                                                                    
      read_reason: str
                                                                                            
  # This decorator tells FastAPI: when someone sends a POST request to /onboarding, run this
   #function
  # async means FastAPI can handle other requests while waiting for Supabase to respond     
@router.post("/onboarding")                                                               
async def onboarding(data: OnboardingData):
                                                                                            
      # Check if someone already signed up with this email
      # .select("id") means only fetch the id column, we don't need everything
      # .eq("email", data.email) means WHERE email = data.email                             
      # .execute() actually runs the query and returns the result
      existing = supabase.table("users").select("id").eq("email", data.email).execute()     
                  
      # existing.data is a list — if it has anything in it, this email is taken             
      if existing.data:
          raise HTTPException(status_code=400, detail="Email already registered")           
                  
      # bcrypt.hashpw takes the password and scrambles it one way — it can never be reversed
      # .encode() converts the string to bytes because bcrypt requires bytes not strings
      # bcrypt.gensalt() generates a random salt — makes every hash unique even for same    
  #password                                                                                  
      # .decode() converts the result back to a string so we can store it in the database   
      password_hash = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()      
                  
      # Insert the user row into the users table                                            
      # This returns the full row that was inserted including the auto-generated id
      user_result = supabase.table("users").insert({                                        
          "name": data.name,
          "email": data.email,                                                              
          "password_hash": password_hash,
          "reading_time": data.reading_time,                                                
          "format": data.format,
          "delivery_time": data.delivery_time,
          "read_reason": data.read_reason,                                                  
      }).execute()
                                                                                            
      # Grab the id of the user we just created                                             
      # We need this to link all the other rows back to this user
      user_id = user_result.data[0]["id"]                                                   
                  
      # Insert one row per source into user_sources                                         
      # List comprehension builds a list of dicts: [{"user_id": ..., "source": "NYT"}, ...]
      if data.sources:                                                                      
          supabase.table("user_sources").insert(
              [{"user_id": user_id, "source": s} for s in data.sources]                     
          ).execute()                                                                       
   
      # Insert one row per interest into user_interests                                     
      # weight starts at 1.0 for everyone — it will change as they use the app
      # parent_topic is null for now — sub-interests will fill this in later                
      # source is "checkbox" because these came from the checkbox list                      
      if data.interests:                                                                    
          supabase.table("user_interests").insert(                                          
              [{"user_id": user_id, "topic": t, "weight": 1.0, "parent_topic": None,        
  "source": "checkbox"} for t in data.interests]                                            
          ).execute()
                                                                                            
      # niche_entities comes in as one string: "Jensen Huang, NVIDIA, Federal Reserve"      
      # .split(",") breaks it into a list: ["Jensen Huang", " NVIDIA", " Federal Reserve"]
      # .strip() removes the spaces around each name                                        
      # the if e.strip() filters out any empty strings in case of trailing commas           
      if data.niche_entities:                                                               
          entities = [e.strip() for e in data.niche_entities.split(",") if e.strip()]       
          if entities:                                                                      
              supabase.table("user_entities").insert(
                  [{"user_id": user_id, "entity_name": e, "weight": 1.0} for e in entities] 
              ).execute()                                                                   
   
      # Send back a success response to the browser with the new user's id                  
      return {"success": True, "user_id": user_id}