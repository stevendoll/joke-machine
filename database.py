import sqlite3
import os
from typing import Optional, List
from datetime import datetime
import uuid
import logging
from contextlib import contextmanager

from models.joke import Joke, JokeCategory

# Set up logging
logger = logging.getLogger(__name__)


class JokeDatabase:
    """SQLite database for persistent joke storage"""

    def __init__(self, db_path: str = None):
        # Use /tmp for Lambda ephemeral storage, local file for development
        if db_path is None:
            if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
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
            conn.execute("""
                CREATE TABLE IF NOT EXISTS jokes (
                    id TEXT PRIMARY KEY,
                    category TEXT NOT NULL,
                    rating REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS steps (
                    id TEXT PRIMARY KEY,
                    role TEXT NOT NULL,
                    order_num INTEGER NOT NULL DEFAULT 1,
                    content TEXT NOT NULL,
                    joke_id TEXT NOT NULL,
                    FOREIGN KEY (joke_id) REFERENCES jokes (id)
                )
            """)
            conn.commit()

    def _seed_sample_data(self):
        """Seed the database with sample jokes if empty"""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) FROM jokes")
            count = cursor.fetchone()[0]

            if count == 0:
                # Sample jokes with steps
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

                # Insert jokes first
                conn.executemany(
                    """
                    INSERT INTO jokes (id, category, rating, created_at)
                    VALUES (?, ?, ?, ?)
                """,
                    sample_jokes,
                )

                # Get joke IDs for steps
                joke_ids = [joke[0] for joke in sample_jokes]

                # Sample steps for each joke
                sample_steps = [
                    # Science joke
                    (
                        str(uuid.uuid4()),
                        "setup",
                        1,
                        "Why don't scientists trust atoms?",
                        joke_ids[0],
                    ),
                    (
                        str(uuid.uuid4()),
                        "punchline",
                        2,
                        "Because they make up everything!",
                        joke_ids[0],
                    ),
                    # General joke 1
                    (
                        str(uuid.uuid4()),
                        "setup",
                        1,
                        "Why did the scarecrow win an award?",
                        joke_ids[1],
                    ),
                    (
                        str(uuid.uuid4()),
                        "punchline",
                        2,
                        "He was outstanding in his field!",
                        joke_ids[1],
                    ),
                    # Food joke
                    (
                        str(uuid.uuid4()),
                        "setup",
                        1,
                        "Why don't eggs tell jokes?",
                        joke_ids[2],
                    ),
                    (
                        str(uuid.uuid4()),
                        "punchline",
                        2,
                        "They'd crack each other up!",
                        joke_ids[2],
                    ),
                    # General joke 2
                    (
                        str(uuid.uuid4()),
                        "setup",
                        1,
                        "What do you call a bear with no teeth?",
                        joke_ids[3],
                    ),
                    (str(uuid.uuid4()), "punchline", 2, "A gummy bear!", joke_ids[3]),
                    # Programming joke 1
                    (
                        str(uuid.uuid4()),
                        "setup",
                        1,
                        "Why do programmers prefer dark mode?",
                        joke_ids[4],
                    ),
                    (
                        str(uuid.uuid4()),
                        "punchline",
                        2,
                        "Because light attracts bugs!",
                        joke_ids[4],
                    ),
                    # Programming joke 2
                    (
                        str(uuid.uuid4()),
                        "setup",
                        1,
                        "Why do Java developers wear glasses?",
                        joke_ids[5],
                    ),
                    (
                        str(uuid.uuid4()),
                        "punchline",
                        2,
                        "Because they don't C#!",
                        joke_ids[5],
                    ),
                    # Programming joke 3
                    (
                        str(uuid.uuid4()),
                        "setup",
                        1,
                        "What's a programmer's favorite hangout spot?",
                        joke_ids[6],
                    ),
                    (str(uuid.uuid4()), "punchline", 2, "The foo bar!", joke_ids[6]),
                    # Tech joke
                    (
                        str(uuid.uuid4()),
                        "setup",
                        1,
                        "Why do programmers always mix up Halloween and Christmas?",
                        joke_ids[7],
                    ),
                    (
                        str(uuid.uuid4()),
                        "punchline",
                        2,
                        "Because Oct 31 equals Dec 25!",
                        joke_ids[7],
                    ),
                ]

                # Insert steps
                conn.executemany(
                    """
                    INSERT INTO steps (id, role, order_num, content, joke_id)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    sample_steps,
                )

                conn.commit()

    def add_joke(self, joke: Joke) -> bool:
        """Add a new joke to the database"""
        max_attempts = 10
        for attempt in range(max_attempts):
            try:
                with self._get_connection() as conn:
                    # Always generate a new ID for each attempt
                    joke.id = str(uuid.uuid4())

                    # Set created_at if not provided
                    if not joke.created_at:
                        joke.created_at = datetime.now()

                    # Insert joke first
                    conn.execute(
                        """
                        INSERT INTO jokes (id, category, rating, created_at)
                        VALUES (?, ?, ?, ?)
                    """,
                        (joke.id, joke.category.value, joke.rating, joke.created_at),
                    )

                    # Insert steps if provided
                    if joke.steps:
                        for step in joke.steps:
                            if not step.id:
                                step.id = str(uuid.uuid4())
                            if not step.joke_id:
                                step.joke_id = joke.id

                            conn.execute(
                                """
                                INSERT INTO steps (id, role, order_num,
                                content, joke_id)
                                VALUES (?, ?, ?, ?, ?)
                            """,
                                (
                                    step.id,
                                    step.role.value,
                                    step.order,
                                    step.content,
                                    step.joke_id,
                                ),
                            )

                    conn.commit()
                    return True
            except sqlite3.IntegrityError:
                # UUID already exists, try again with new UUID
                if attempt == max_attempts - 1:
                    # Last attempt failed
                    return False
            except sqlite3.Error as e:
                logger.error(f"Database error: {e}")
                return False

        return False

    def get_joke_by_id(self, joke_id: str) -> Optional[Joke]:
        """Get a specific joke by ID"""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM jokes WHERE id = ?", (joke_id,))
            row = cursor.fetchone()

            if row:
                # Get steps for this joke
                steps_cursor = conn.execute(
                    "SELECT * FROM steps WHERE joke_id = ? ORDER BY order_num",
                    (joke_id,),
                )
                steps_rows = steps_cursor.fetchall()

                # Convert to Step objects
                from models.joke import Step, StepRole

                steps = []
                for step_row in steps_rows:
                    steps.append(
                        Step(
                            id=step_row["id"],
                            role=StepRole(step_row["role"]),
                            order=step_row["order_num"],
                            content=step_row["content"],
                            joke_id=step_row["joke_id"],
                        )
                    )

                return Joke(
                    id=row["id"],
                    category=JokeCategory(row["category"]),
                    rating=row["rating"],
                    created_at=row["created_at"],
                    steps=steps,
                )
            return None

    def get_jokes(
        self, category: Optional[JokeCategory] = None, count: int = 10
    ) -> List[Joke]:
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
                # Get steps for this joke
                steps_cursor = conn.execute(
                    "SELECT * FROM steps WHERE joke_id = ? ORDER BY order_num",
                    (row["id"],),
                )
                steps_rows = steps_cursor.fetchall()

                # Convert to Step objects
                from models.joke import Step, StepRole

                steps = []
                for step_row in steps_rows:
                    steps.append(
                        Step(
                            id=step_row["id"],
                            role=StepRole(step_row["role"]),
                            order=step_row["order_num"],
                            content=step_row["content"],
                            joke_id=step_row["joke_id"],
                        )
                    )

                jokes.append(
                    Joke(
                        id=row["id"],
                        category=JokeCategory(row["category"]),
                        rating=row["rating"],
                        created_at=row["created_at"],
                        steps=steps,
                    )
                )

            return jokes

    def get_all_jokes(self) -> List[Joke]:
        """Get all jokes from the database"""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT * FROM jokes ORDER BY created_at")
            rows = cursor.fetchall()

            jokes = []
            for row in rows:
                # Get steps for this joke
                steps_cursor = conn.execute(
                    "SELECT * FROM steps WHERE joke_id = ? ORDER BY order_num",
                    (row["id"],),
                )
                steps_rows = steps_cursor.fetchall()

                # Convert to Step objects
                from models.joke import Step, StepRole

                steps = []
                for step_row in steps_rows:
                    steps.append(
                        Step(
                            id=step_row["id"],
                            role=StepRole(step_row["role"]),
                            order=step_row["order_num"],
                            content=step_row["content"],
                            joke_id=step_row["joke_id"],
                        )
                    )

                jokes.append(
                    Joke(
                        id=row["id"],
                        category=JokeCategory(row["category"]),
                        rating=row["rating"],
                        created_at=row["created_at"],
                        steps=steps,
                    )
                )

            return jokes

    def update_joke_rating(self, joke_id: str, rating: float) -> bool:
        """Update the rating of a joke"""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    """
                    UPDATE jokes SET rating = ? WHERE id = ?
                """,
                    (rating, joke_id),
                )
                conn.commit()
                return (
                    cursor.rowcount > 0
                )  # Return True only if a row was actually updated
        except sqlite3.Error:
            return False

    def delete_joke(self, joke_id: str) -> bool:
        """Delete a joke from the database"""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    """
                DELETE FROM jokes WHERE id = ?
            """,
                    (joke_id,),
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error:
            return False


# Global database instance
db = JokeDatabase()
