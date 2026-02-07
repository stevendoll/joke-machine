import sqlite3
import json
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
from models.joke import Joke, JokeCategory, JokeType
import os
import random
import uuid

class JokeDatabase:
    """SQLite database for persistent joke storage"""
    
    def __init__(self, db_path: str = None):
        # Use /tmp for Lambda ephemeral storage, local file for development
        if db_path is None:
            if os.environ.get('AWS_LAMBDA_FUNCTION_NAME'):
                self.db_path = "/tmp/jokes.db"
            else:
                self.db_path = "jokes.db"
        else:
            self.db_path = db_path
        
        self._init_database()
        self._seed_sample_data()
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def _init_database(self):
        """Initialize the database schema"""
        with self._get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS jokes (
                    uuid TEXT PRIMARY KEY,
                    id TEXT UNIQUE,
                    setup TEXT NOT NULL,
                    punchline TEXT NOT NULL,
                    category TEXT NOT NULL,
                    rating REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
    
    def _seed_sample_data(self):
        """Seed the database with sample jokes if empty"""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM jokes")
            count = cursor.fetchone()[0]
            
            if count == 0:
                sample_jokes = [
                    (str(uuid.uuid4()), "gen_001", "Why don't scientists trust atoms?", "Because they make up everything!", "science", None),
                    (str(uuid.uuid4()), "gen_002", "Why did the scarecrow win an award?", "He was outstanding in his field!", "general", None),
                    (str(uuid.uuid4()), "gen_003", "Why don't eggs tell jokes?", "They'd crack each other up!", "food", None),
                    (str(uuid.uuid4()), "gen_004", "What do you call a bear with no teeth?", "A gummy bear!", "general", None),
                    (str(uuid.uuid4()), "tech_001", "Why do programmers prefer dark mode?", "Because light attracts bugs!", "programming", None),
                    (str(uuid.uuid4()), "tech_002", "Why do Java developers wear glasses?", "Because they don't C#!", "programming", None),
                    (str(uuid.uuid4()), "tech_003", "What's a programmer's favorite hangout spot?", "The foo bar!", "programming", None),
                    (str(uuid.uuid4()), "tech_004", "Why do programmers always mix up Halloween and Christmas?", "Because Oct 31 equals Dec 25!", "tech", None),
                ]
                
                conn.executemany('''
                    INSERT INTO jokes (uuid, id, setup, punchline, category, rating)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', sample_jokes)
                conn.commit()
    
    def add_joke(self, joke: Joke) -> bool:
        """Add a new joke to the database"""
        try:
            with self._get_connection() as conn:
                # Generate UUID and ID if not provided
                if not joke.uuid:
                    joke.uuid = str(uuid.uuid4())
                if not joke.id:
                    joke.id = f"user_{random.randint(1000, 9999)}"
                
                conn.execute('''
                    INSERT INTO jokes (uuid, id, setup, punchline, category, rating)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (joke.uuid, joke.id, joke.setup, joke.punchline, joke.category.value, joke.rating))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False
    
    def get_joke_by_id(self, joke_id: str) -> Optional[Joke]:
        """Get a specific joke by ID"""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM jokes WHERE id = ?", (joke_id,))
            row = cursor.fetchone()
            
            if row:
                return Joke(
                    uuid=row['uuid'],
                    id=row['id'],
                    setup=row['setup'],
                    punchline=row['punchline'],
                    category=JokeCategory(row['category']),
                    rating=row['rating']
                )
            return None
    
    def get_jokes(self, joke_type: Optional[JokeType] = None, category: Optional[JokeCategory] = None, count: int = 10) -> List[Joke]:
        """Get jokes filtered by type and category"""
        query = "SELECT * FROM jokes"
        params = []
        
        # Build WHERE clause
        conditions = []
        
        # If category is specified, always filter by it first
        if category:
            conditions.append("category = ?")
            params.append(category.value)
        
        # If type is also specified, add type filtering
        if joke_type:
            # Map joke types to categories
            type_categories = {
                JokeType.GENERAL: [JokeCategory.GENERAL, JokeCategory.SCIENCE, JokeCategory.FOOD],
                JokeType.TECH: [JokeCategory.PROGRAMMING, JokeCategory.TECH]
            }
            
            if joke_type in type_categories:
                category_placeholders = ",".join(["?" for _ in type_categories[joke_type]])
                if conditions:
                    conditions.append(f"category IN ({category_placeholders})")
                else:
                    conditions.append(f"category IN ({category_placeholders})")
                params.extend([cat.value for cat in type_categories[joke_type]])
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        # Add random ordering and limit
        query += " ORDER BY RANDOM() LIMIT ?"
        params.append(count)
        
        with self._get_connection() as conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            jokes = []
            for row in rows:
                jokes.append(Joke(
                    uuid=row['uuid'],
                    id=row['id'],
                    setup=row['setup'],
                    punchline=row['punchline'],
                    category=JokeCategory(row['category']),
                    rating=row['rating']
                ))
            
            return jokes
    
    def get_all_jokes(self) -> List[Joke]:
        """Get all jokes from the database"""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM jokes ORDER BY created_at")
            rows = cursor.fetchall()
            
            jokes = []
            for row in rows:
                jokes.append(Joke(
                    uuid=row['uuid'],
                    id=row['id'],
                    setup=row['setup'],
                    punchline=row['punchline'],
                    category=JokeCategory(row['category']),
                    rating=row['rating']
                ))
            
            return jokes
    
    def update_joke_rating(self, joke_id: str, rating: float) -> bool:
        """Update the rating of a joke"""
        try:
            with self._get_connection() as conn:
                conn.execute('''
                    UPDATE jokes SET rating = ? WHERE id = ?
                ''', (rating, joke_id))
                conn.commit()
                return True
        except:
            return False
    
    def delete_joke(self, joke_id: str) -> bool:
        """Delete a joke from the database"""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("DELETE FROM jokes WHERE id = ?", (joke_id,))
                conn.commit()
                return cursor.rowcount > 0
        except:
            return False

# Global database instance
db = JokeDatabase()
