TITLE_BLOCKLIST = [
      "morning briefing",                                                       
      "daily crunch",
      "week in review",                                                         
      "newsletter",
      "roundup",                                                              
      "podcast",
      "listen:",
      "what we learned",                      
      "five things",                      
      "this week in",
      "Morning news brief"
]                                                                             
   
NPR_BLOCKLIST = ["listen:", "listen now", "tiny desk", "shots -"]             
TECHCRUNCH_BLOCKLIST = ["daily crunch", "week in review", "this week"]
                                                                              
def should_skip(title: str, source: str = "") -> bool:                        
    lower = title.lower()               
    for phrase in TITLE_BLOCKLIST:                                            
        if phrase in lower:                                                   
            return True                                                     
    if source == "techcrunch":                                                
        for phrase in TECHCRUNCH_BLOCKLIST:
            if phrase in lower:                                             
                return True             
    if source == "npr":
        for phrase in NPR_BLOCKLIST:                                          
            if phrase in lower:
                return True                                                   
    return False