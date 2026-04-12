# YourNews — Product Decisions

## Decision 1: Onboarding questions
Date: April 11 2026
Decision: Two questions only
  Q1: What are you interested in staying informed on?
      (max 3 lines)
  Q2: What do you wish you understood better?
      (optional)
Why: Free text gives us both entities and 
     concepts. 
Status: DECIDED

## Decision 2: Initial weights
Date: April 1q 2026
Decision: All interests start equal weight - still havents decided
Status: TBD

## Decision 3: Agent role
Date: TBD
Decision: TBD
Status: OPEN

## Poshitha work 
## Decision: Onboarding data structure (April 12 2026)
Status: DONE
What the form sends:
{
  "name": "...",
  "email": "...",
  "password": "...",
  "interests": "free text from Q1",
  "learning_goals": "free text from Q2",
  "reading_time": "...",
  "delivery_time": "..."
}
Tables that get populated on signup:
- users (name, email, password_hash, interests_raw, learning_goals_raw)
- user_interests (parsed topics)
- user_entities (parsed named entities)