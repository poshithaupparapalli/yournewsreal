from fastapi import FastAPI                                                               
from fastapi.middleware.cors import CORSMiddleware                                        
from routes.auth import router as auth_router                                             
                  
  # Create the FastAPI app — this is the actual server                                      
app = FastAPI() 
                                                                                            
  # CORS middleware tells the server to accept requests from the browser
  # Without this the browser will block the request even if FastAPI is running
  # allow_origins=["*"] means accept requests from any URL                                  
  # Later when you deploy you will change this to just your frontend URL                    
app.add_middleware(                                                                       
      CORSMiddleware,                                                                       
      allow_origins=["*"],                                                                  
      allow_credentials=True,                                                               
      allow_methods=["*"],
      allow_headers=["*"],
  )

  # Register the auth router — this plugs in all routes defined in routes/auth.py           
  # Now POST /onboarding exists on this server
app.include_router(auth_router)                                                           
                  
  # A simple root route so you can check the server is running                              
  # Open http://localhost:8000 in your browser and you should see this
@app.get("/")                                                                             
def root():     
      return {"status": "YourNews backend is running"} 