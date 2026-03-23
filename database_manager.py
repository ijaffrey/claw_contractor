from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from database import Base, User, Transaction, Account
import os
from typing import Optional, List, Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, database_url: Optional[str] = None):
        """Initialize the DatabaseManager with SQLAlchemy session."""
        if database_url is None:
            database_url = os.getenv('DATABASE_URL', 'sqlite:///patrick.db')
        
        self.engine = create_engine(database_url, echo=False)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        logger.info(f"DatabaseManager initialized with URL: {database_url}")

    def create_user(self, name: str, email: str, **kwargs) -> bool:
        """Create a new user in the database."""
        try:
            existing_user = self.session.query(User).filter_by(email=email).first()
            if existing_user:
                logger.warning(f"User with email {email} already exists")
                return False
            
            new_user = User(name=name, email=email, **kwargs)
            self.session.add(new_user)
            self.session.commit()
            logger.info(f"User {name} created successfully")
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error creating user: {e}")
            return False

    def get_user(self, user_id: Optional[int] = None, email: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve a user by ID or email."""
        try:
            if user_id:
                user = self.session.query(User).filter_by(id=user_id).first()
            elif email:
                user = self.session.query(User).filter_by(email=email).first()
            else:
                logger.error("Either user_id or email must be provided")
                return None
            
            if user:
                return {
                    'id': user.id,
                    'name': user.name,
                    'email': user.email,
                    'created_at': user.created_at
                }
            return None
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving user: {e}")
            return None

    def update_user(self, user_id: int, **kwargs) -> bool:
        """Update user information."""
        try:
            user = self.session.query(User).filter_by(id=user_id).first()
            if not user:
                logger.warning(f"User with ID {user_id} not found")
                return False
            
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            
            self.session.commit()
            logger.info(f"User {user_id} updated successfully")
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error updating user: {e}")
            return False

    def delete_user(self, user_id: int) -> bool:
        """Delete a user from the database."""
        try:
            user = self.session.query(User).filter_by(id=user_id).first()
            if not user:
                logger.warning(f"User with ID {user_id} not found")
                return False
            
            self.session.delete(user)
            self.session.commit()
            logger.info(f"User {user_id} deleted successfully")
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error deleting user: {e}")
            return False

    def create_transaction(self, user_id: int, amount: float, description: str, transaction_type: str = 'expense', account_id: Optional[int] = None) -> bool:
        """Create a new transaction."""
        try:
            # Verify user exists
            user = self.session.query(User).filter_by(id=user_id).first()
            if not user:
                logger.error(f"User with ID {user_id} not found")
                return False
            
            # Verify account exists if provided
            if account_id:
                account = self.session.query(Account).filter_by(id=account_id).first()
                if not account:
                    logger.error(f"Account with ID {account_id} not found")
                    return False
            
            new_transaction = Transaction(
                user_id=user_id,
                amount=amount,
                description=description,
                transaction_type=transaction_type,
                account_id=account_id
            )
            self.session.add(new_transaction)
            self.session.commit()
            logger.info(f"Transaction created for user {user_id}")
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error creating transaction: {e}")
            return False

    def get_transactions(self, user_id: int, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Retrieve transactions for a user."""
        try:
            query = self.session.query(Transaction).filter_by(user_id=user_id).order_by(Transaction.created_at.desc())
            
            if limit:
                query = query.limit(limit)
            
            transactions = query.all()
            return [
                {
                    'id': t.id,
                    'user_id': t.user_id,
                    'amount': t.amount,
                    'description': t.description,
                    'transaction_type': t.transaction_type,
                    'account_id': t.account_id,
                    'created_at': t.created_at
                }
                for t in transactions
            ]
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving transactions: {e}")
            return []

    def create_account(self, user_id: int, name: str, account_type: str = 'checking', balance: float = 0.0) -> bool:
        """Create a new account for a user."""
        try:
            # Verify user exists
            user = self.session.query(User).filter_by(id=user_id).first()
            if not user:
                logger.error(f"User with ID {user_id} not found")
                return False
            
            new_account = Account(
                user_id=user_id,
                name=name,
                account_type=account_type,
                balance=balance
            )
            self.session.add(new_account)
            self.session.commit()
            logger.info(f"Account {name} created for user {user_id}")
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error creating account: {e}")
            return False

    def get_accounts(self, user_id: int) -> List[Dict[str, Any]]:
        """Retrieve all accounts for a user."""
        try:
            accounts = self.session.query(Account).filter_by(user_id=user_id).all()
            return [
                {
                    'id': a.id,
                    'user_id': a.user_id,
                    'name': a.name,
                    'account_type': a.account_type,
                    'balance': a.balance,
                    'created_at': a.created_at
                }
                for a in accounts
            ]
        except SQLAlchemyError as e:
            logger.error(f"Error retrieving accounts: {e}")
            return []

    def update_account_balance(self, account_id: int, new_balance: float) -> bool:
        """Update the balance of an account."""
        try:
            account = self.session.query(Account).filter_by(id=account_id).first()
            if not account:
                logger.warning(f"Account with ID {account_id} not found")
                return False
            
            account.balance = new_balance
            self.session.commit()
            logger.info(f"Account {account_id} balance updated to {new_balance}")
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error updating account balance: {e}")
            return False

    def execute_query(self, query: str, params: Optional[Dict] = None) -> Optional[List[Dict[str, Any]]]:
        """Execute a raw SQL query and return results."""
        try:
            if params is None:
                params = {}
            
            result = self.session.execute(text(query), params)
            
            # Check if it's a SELECT query (has fetchable results)
            if result.returns_rows:
                rows = result.fetchall()
                columns = result.keys()
                return [dict(zip(columns, row)) for row in rows]
            else:
                # For INSERT, UPDATE, DELETE queries
                self.session.commit()
                return None
        except SQLAlchemyError as e:
            self.session.rollback()
            logger.error(f"Error executing query: {e}")
            return None

    def close(self):
        """Close the database session."""
        if self.session:
            self.session.close()
            logger.info("Database session closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()