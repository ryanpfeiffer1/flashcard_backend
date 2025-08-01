from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
import ollama
import json

import models
from database import SessionLocal, engine

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# DB session dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Ollama client pointing to your local server
ollama_client = ollama.Client(host='http://192.168.0.251:11434')

def generate_flashcards(topic: str) -> list[tuple[str, str]]:
    prompt = f"""Generate 10 educational flashcards about the topic "{topic}".
Respond only in this JSON format (no extra text):
[
  {{ "front": "Question or term?", "back": "Answer or explanation." }},
  ...
]
"""
    try:
        response = ollama_client.chat(
            model="phi4:mini",
            messages=[{"role": "user", "content": prompt}]
        )
        content = response['message']['content']

        # Parse JSON flashcards list
        flashcards = json.loads(content)

        # Validate and return as list of (front, back)
        return [(card["front"], card["back"]) for card in flashcards]

    except Exception as e:
        raise RuntimeError(f"Failed to generate flashcards: {e}")

# Pydantic schemas
class FlashcardCreate(BaseModel):
    topic: str
    front: str
    back: str

class FlashcardOut(BaseModel):
    id: int
    topic: str
    front: str
    back: str

    class Config:
        orm_mode = True

class TopicInput(BaseModel):
    topic_text: str

# Endpoint: create flashcard manually
@app.post("/flashcards/", response_model=FlashcardOut)
def create_flashcard(flashcard: FlashcardCreate, db: Session = Depends(get_db)):
    db_card = models.Flashcard(**flashcard.dict())
    db.add(db_card)
    db.commit()
    db.refresh(db_card)
    return db_card

# Endpoint: get flashcard by id
@app.get("/flashcards/{flashcard_id}", response_model=FlashcardOut)
def read_flashcard(flashcard_id: int, db: Session = Depends(get_db)):
    card = db.query(models.Flashcard).filter(models.Flashcard.id == flashcard_id).first()
    if card is None:
        raise HTTPException(status_code=404, detail="Flashcard not found")
    return card

# Endpoint: list flashcards with pagination
@app.get("/flashcards/", response_model=list[FlashcardOut])
def list_flashcards(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    cards = db.query(models.Flashcard).offset(skip).limit(limit).all()
    return cards

# Endpoint: generate flashcards from topic text and store in DB
@app.post("/generate/")
def generate_and_store(input: TopicInput, db: Session = Depends(get_db)):
    try:
        flashcards = generate_flashcards(input.topic_text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    for front, back in flashcards:
        card = models.Flashcard(topic=input.topic_text, front=front, back=back)
        db.add(card)

    db.commit()
    return {"message": f"{len(flashcards)} flashcards stored."}
