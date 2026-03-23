--
CREATE TABLE users(
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  name text,
  email text,
  date_created timestamptz DEFAULT now()
);

CREATE TABLE user_interests (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id uuid REFERENCES users(id),
  topic text,
  preference_vector vector(1536),
  created_at timestamptz DEFAULT now()
);



