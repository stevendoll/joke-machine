import sqlite3
import json
from typing import List, Optional, Dict, Any
from contextlib import contextmanager
from models.joke import Joke, JokeCategory
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
                    (str(uuid.uuid4()), "science", None, None),
                    (str(uuid.uuid4()), "general", None, None),
                    (str(uuid.uuid4()), "food", None, None),
                    (str(uuid.uuid4()), "general", None, None),
                    (str(uuid.uuid4()), "programming", None, None),
                    (str(uuid.uuid4()), "programming", None, None),
                    (str(uuid.uuid4()), "programming", None, None),
                    (str(uuid.uuid4()), "tech", None, None),
                ]
                
                conn.executemany('''
                    INSERT INTO jokes (uuid, category, rating, created_at)
                    VALUES (?, ?, ?, ?)
                ''', sample_jokes)
                conn.commit()
    
    def add_joke(self, joke: Joke) -> bool:
        """Add a new joke to the database"""
        max_attempts = 10
        for attempt in range(max_attempts):
            try:
                with self._get_connection() as conn:
                    # Generate UUID if not provided
                    if not joke.uuid:
                        joke.uuid = str(uuid.uuid4())
                    
                    # Set created_at if not provided
                    if not joke.created_at:
                        from datetime import datetime, timezone
                        joke.created_at = datetime.now(timezone.utc)
                    
                    conn.execute('''
                        INSERT INTO jokes (uuid, category, rating, created_at)
                        VALUES (?, ?, ?, ?)
                    ''', (joke.uuid, joke.category.value, joke.rating, joke.created_at))
                    conn.commit()
                    return True
            except sqlite3.IntegrityError:
                # UUID already exists, generate a new one and try again
                joke.uuid = str(uuid.uuid4())
                continue
        
        return False
    
    def get_joke_by_id(self, joke_id: str) -> Optional[Joke]:
        """Get a specific joke by ID"""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM jokes WHERE uuid = ?", (joke_id,))
            row = cursor.fetchone()
            
            if row:
                return Joke(
                    uuid=row['uuid'],
                    category=JokeCategory(row['category']),
                    rating=row['rating'],
                    created_at=row['created_at']
                )
            return None
    
    def get_jokes(self, category: Optional[JokeCategory] = None, count: int = 10) -> List[Joke]:
        """Get jokes filtered by category"""
        query = "SELECT * FROM jokes"
        params = []
        
        # Build WHERE clause
        conditions = []
        
        # If category is specified, filter by it
        if category:
            conditions.append("category = ?")
            params.append(category.value)
        
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
                    category=JokeCategory(row['category']),
                    rating=row['rating'],
                    created_at=row['created_at']
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
                    category=JokeCategory(row['category']),
                    rating=row['rating'],
                    created_at=row['created_at']
                ))
            
            return jokes
    
    def update_joke_rating(self, joke_id: str, rating: float) -> bool:
        """Update the rating of a joke"""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute('''
                    UPDATE jokes SET rating = ? WHERE uuid = ?
                ''', (rating, joke_id))
                conn.commit()
                return cursor.rowcount > 0  # Return True only if a row was actually updated
        except:
            return False
    
    def delete_joke(self, joke_id: str) -> bool:
        """Delete a joke from the database"""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("DELETE FROM jokes WHERE uuid = ?", (joke_id,))
                conn.commit()
                return cursor.rowcount > 0
        except:
            return False

# Global database instance
db = JokeDatabase()
