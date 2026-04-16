import os
import sys
import logging
from sqlalchemy import text
from database import create_database_engine, get_db_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Create projects and project_enrichments tables"""
    try:
        engine = create_database_engine()
        
        # Read and execute projects table SQL
        with open('infrastructure/create_projects_table.sql', 'r') as f:
            projects_sql = f.read()
        
        # Read and execute project_enrichments table SQL
        with open('infrastructure/create_project_enrichments_table.sql', 'r') as f:
            enrichments_sql = f.read()
        
        with engine.connect() as conn:
            # Execute projects table creation
            logger.info("Creating projects table...")
            conn.execute(text(projects_sql))
            conn.commit()
            
            # Execute project_enrichments table creation
            logger.info("Creating project_enrichments table...")
            conn.execute(text(enrichments_sql))
            conn.commit()
            
            logger.info("Successfully created projects tables")
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

if __name__ == '__main__':
    run_migration()