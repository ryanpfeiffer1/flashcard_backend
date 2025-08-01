from sqlalchemy import Column, Integer, String
from database import Base, engine
import models
class Flashcard(Base):
    __tablename__ = "flashcards"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String)
    front = Column(String)
    back = Column(String)
models.Base.metadata.create_all(bind=engine)
