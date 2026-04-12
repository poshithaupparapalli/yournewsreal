from fastapi import APIRouter, HTTPException                                              
from pydantic import BaseModel                                                                                                                            
import bcrypt                                                                             
from database.connection import supabase
                                                                                            
  # APIRouter lets us define routes in a separate file from main.py                         
  # Think of it as a mini-app that main.py will plug in                                     
router = APIRouter()                                                                      
                  
# This defines the new shape of JSON we expect from the browser                                                                                           
# Much simpler than before — just two free text fields instead of checkboxes
class OnboardingData(BaseModel):                                                                                                                          
    name: str   
    email: str                                                                                                                                            
    password: str
    interests: str        # raw free text e.g. "Jensen Huang, NVIDIA, Formula 1"
    learning_goals: str   # raw free text e.g. "geopolitics, quantum computing"
                                                                                            
  # This decorator tells FastAPI: when someone sends a POST request to /onboarding, run this
   #function
  # async means FastAPI can handle other requests while waiting for Supabase to respond     
@router.post("/onboarding")                                                               
async def onboarding(data: OnboardingData):
                                                                                            
      # Check if someone already signed up with this email
      # .select("id") means only fetch the id column, we don't need everything
      # .eq("email", data.email) means WHERE email = data.email                             
      # .execute() actually runs the query and returns the result
        # Check if this email already has an account                                                                                                          
    existing = supabase.table("users").select("id").eq("email", data.email).execute()
    if existing.data:                                                                                                                                     
        raise HTTPException(status_code=400, detail="Email already registered")             
                  
      # bcrypt.hashpw takes the password and scrambles it one way — it can never be reversed
      # .encode() converts the string to bytes because bcrypt requires bytes not strings
      # bcrypt.gensalt() generates a random salt — makes every hash unique even for same    
  #password                                                                                  
      # .decode() converts the result back to a string so we can store it in the database   
    password_hash = bcrypt.hashpw(data.password.encode(), bcrypt.gensalt()).decode()                  
    # Save the user row with the raw interest text                                                                                                        
      # We store exactly what they typed — LLM will parse it later                                                                                          
    user_result = supabase.table("users").insert({                                                                                                        
        "name": data.name,
        "email": data.email,                                                                                                                              
        "password_hash": password_hash,
        "interests_raw": data.interests,                                                                                                                  
        "learning_goals_raw": data.learning_goals,
    }).execute()
                                                                                            
    # Grab the new user's id — we'll send it back so the frontend knows who signed up                                                                     
    user_id = user_result.data[0]["id"]
                                                                                                                                                            
    return {"success": True, "user_id": user_id}


#O nboardingData now only has 5 fields instead of 10 - name, email, password, interests, learning_goals
# removed all the sources, niche_entities, reading_time etc. — that data no longer comes from the form                                                 
# insert now saves to interests_raw and learning_goals_raw — the two new columns you just added                                                       
# Everything else stays the same like password hashing, email check, returning the user id                                                                   