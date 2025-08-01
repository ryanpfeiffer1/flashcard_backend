from database import SessionLocal
from models import Flashcard

def test_database():
    db = SessionLocal()

    # Create a test flashcard
    test_card = Flashcard(topic="Test Topic", front="What is 2+2?", back="4")
    
    # Add and commit
    db.add(test_card)
    db.commit()

    # Query the flashcard back
    card = db.query(Flashcard).filter_by(topic="Test Topic").first()

    if card:
        print(f"Flashcard retrieved: Q: {card.front} A: {card.back}")
    else:
        print("No flashcard found")

    db.close()

if __name__ == "__main__":
    test_database()
