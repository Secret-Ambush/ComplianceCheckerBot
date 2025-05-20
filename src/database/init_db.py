import logging
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.config import DATABASE_URL, Base
from src.database.models import Document, LineItem, Rule, ValidationReport

logger = logging.getLogger(__name__)


def init_db():
    """Initialize database."""
    try:
        # Create database engine
        engine = create_engine(DATABASE_URL)
        
        # Create tables
        Base.metadata.create_all(bind=engine)
        
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise


def drop_db():
    """Drop all tables from database."""
    try:
        # Create database engine
        engine = create_engine(DATABASE_URL)
        
        # Drop tables
        Base.metadata.drop_all(bind=engine)
        
        logger.info("Database dropped successfully")
        
    except Exception as e:
        logger.error(f"Error dropping database: {str(e)}")
        raise


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Initialize database
    init_db() 