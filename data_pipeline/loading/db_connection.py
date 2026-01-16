"""
Database Connection Management
Handles PostgreSQL connections with connection pooling
"""
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Optional
from utils.config import db_config
from utils.logger import logger


class DatabaseConnection:
    """
    Manages PostgreSQL database connections
    Uses connection pooling for efficiency
    """
    
    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        database: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
        min_connections: int = 1,
        max_connections: int = 5
    ):
        """
        Initialize database connection pool
        
        Args:
            host: Database host (defaults to config)
            port: Database port (defaults to config)
            database: Database name (defaults to config)
            user: Database user (defaults to config)
            password: Database password (defaults to config)
            min_connections: Minimum pool size
            max_connections: Maximum pool size
        """
        self.host = host or db_config.host
        self.port = port or db_config.port
        self.database = database or db_config.name
        self.user = user or db_config.user
        self.password = password or db_config.password
        
        self.connection_pool: Optional[pool.ThreadedConnectionPool] = None
        self.min_connections = min_connections
        self.max_connections = max_connections
        
        logger.info(f"DatabaseConnection initialized for {self.user}@{self.host}:{self.port}/{self.database}")
    
    def create_pool(self):
        """Create connection pool"""
        try:
            self.connection_pool = pool.ThreadedConnectionPool(
                minconn=self.min_connections,
                maxconn=self.max_connections,
                host=self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password
            )
            logger.info("Connection pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create connection pool: {e}")
            raise
    
    def get_connection(self):
        """Get a connection from the pool"""
        if not self.connection_pool:
            self.create_pool()
        
        try:
            return self.connection_pool.getconn()
        except Exception as e:
            logger.error(f"Failed to get connection from pool: {e}")
            raise
    
    def return_connection(self, conn):
        """Return a connection to the pool"""
        if self.connection_pool:
            try:
                self.connection_pool.putconn(conn)
            except Exception as e:
                logger.warning(f"Error returning connection to pool: {e}")
    
    @contextmanager
    def get_cursor(self, cursor_factory=RealDictCursor):
        """
        Context manager for database cursor
        
        Usage:
            with db.get_cursor() as cursor:
                cursor.execute("SELECT * FROM ...")
        """
        conn = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor(cursor_factory=cursor_factory)
            yield cursor
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database operation failed: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.return_connection(conn)
    
    def close_pool(self):
        """Close all connections in the pool"""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("Connection pool closed")
    
    def test_connection(self) -> bool:
        """Test database connection"""
        cursor = None
        try:
            with self.get_cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                logger.info("Database connection test successful")
                return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
