from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# --- Database Setup ---
DATABASE_URL = 'sqlite:///bar_audit.db'
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db_session = Session()
Base = declarative_base()

# This module provides the database connection and base for models.
# Other modules will import db_session and Base from here.
