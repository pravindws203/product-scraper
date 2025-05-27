"""
MySQL Database Handler Module
Author: Pravin Prajapati
A modular database handler for Product_Webscrapping database operations
"""

import mysql.connector
import json
from logger_config import setup_logger
from typing import List, Dict, Optional, Union


class MySQLDB:
  def __init__(self, host: str = "10.0.101.153", user: str = "root",
               password: str = "Admin@123", database: str = "Product_Webscrapping"):
    """
    Initialize the database handler

    Args:
        host (str): Database host
        user (str): Database username
        password (str): Database password
        database (str): Database name
    """
    self.host = host
    self.user = user
    self.password = password
    self.database = database
    self.connection = None
    self._setup_logging()
  
  def _setup_logging(self):
    """Configure logging settings"""
    self.logger = setup_logger("MySQLDB", "mysql_db_handle.log")
    
  def _connect(self) -> bool:
    """Establish database connection"""
    try:
      self.connection = mysql.connector.connect(
        host=self.host,
        port=3306,
        password=self.password,
        database=self.database
      )
      self.logger.info("Database connection established")
      return True
    except mysql.connector.Error as err:
      self.logger.error(f"Database connection error: {err}")
      return False
  
  def _disconnect(self):
    """Close database connection"""
    if self.connection and self.connection.is_connected():
      self.logger.warning("Closing database connection")
      self.connection.close()
  
  def fetch_scraped_images(self) -> List[Dict[str, str]]:
    """
    Fetch scraped product images from database

    Returns:
        List of dictionaries containing image URLs for each product
    """
    query = """
            SELECT scrapping_id, image_url_1, image_url_2, image_url_3, image_url_4, image_url_5,
                   image_url_6, image_url_7, image_url_8, image_url_9, image_url_10,
                   image_url_11, image_url_12, image_url_13, image_url_14, image_url_15
            FROM scraped_product
            WHERE unit_of_measure != 'COMBO'
        """
    columns = [
      'scrapping_id', 'image_url_1', 'image_url_2', 'image_url_3', 'image_url_4', 'image_url_5',
      'image_url_6', 'image_url_7', 'image_url_8', 'image_url_9', 'image_url_10',
      'image_url_11', 'image_url_12', 'image_url_13', 'image_url_14', 'image_url_15'
    ]
    return self._execute_query(query, columns)
  
  def get_data(self, table: str, columns: List[str] = ['*'],
               where: Optional[str] = None) -> List[Dict[str, Union[str, int, float, dict]]]:
    """
    Generic method to get data from any table

    Args:
        table (str): Table name
        columns (List[str]): List of columns to select
        where (Optional[str]): WHERE clause (without the WHERE keyword)

    Returns:
        List of dictionaries containing the query results
    """
    cols = ', '.join(columns)
    query = f"SELECT {cols} FROM {table}"
    if where:
      query += f" WHERE {where}"
    
    try:
      if not self._connect():
        return []
      
      cursor = self.connection.cursor(dictionary=True)
      cursor.execute(query)
      rows = cursor.fetchall()
      
      # Convert JSON strings back to dictionaries
      processed_rows = []
      for row in rows:
        processed_row = {}
        for key, value in row.items():
          try:
            if isinstance(value, str) and (value.startswith('{') or value.startswith('[')):
              processed_row[key] = json.loads(value)
            else:
              processed_row[key] = value
          except json.JSONDecodeError:
            processed_row[key] = value
        processed_rows.append(processed_row)
      
      return processed_rows
    
    except mysql.connector.Error as err:
      print(f"Query error: {err}")
      return []
    finally:
      if cursor:
        cursor.close()
      self._disconnect()
  
  def insert_data(self, table: str, data: Dict[str, Union[str, int, float, dict]]) -> int:
    """
    Insert data into a table

    Args:
        table (str): Table name
        data (Dict): Dictionary of column-value pairs

    Returns:
        int: The ID of the inserted row
    """
    # Convert dictionaries to JSON strings
    processed_data = {}
    for key, value in data.items():
      if isinstance(value, dict):
        processed_data[key] = json.dumps(value)
      else:
        processed_data[key] = value
    
    columns = ', '.join(processed_data.keys())
    placeholders = ', '.join(['%s'] * len(processed_data))
    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    
    try:
      if not self._connect():
        return 0
      
      cursor = self.connection.cursor()
      cursor.execute(query, tuple(processed_data.values()))
      self.connection.commit()
      return cursor.lastrowid
    
    except mysql.connector.Error as err:
      print(f"Insert error: {err}")
      return 0
    finally:
      if cursor:
        cursor.close()
      self._disconnect()
  
  def update_data(self, table: str, data: Dict[str, Union[str, int, float]],
                  where: str) -> bool:
    """
    Update data in a table

    Args:
        table (str): Table name
        data (Dict): Dictionary of column-value pairs to update
        where (str): WHERE clause (without the WHERE keyword)

    Returns:
        bool: True if update was successful, False otherwise
    """
    set_clause = ', '.join([f"{key} = %s" for key in data.keys()])
    query = f"UPDATE {table} SET {set_clause} WHERE {where}"
    try:
      if not self._connect():
        return False
      
      cursor = self.connection.cursor()
      cursor.execute(query, tuple(data.values()))
      self.connection.commit()
      self.logger.info(f"Data updated {table} successfully")
      return cursor.rowcount > 0
    
    except mysql.connector.Error as err:
      self.logger.error(f"Update error: {err}")
      return False
    finally:
      if cursor:
        cursor.close()
      self._disconnect()
  
  def _execute_query(self, query: str, columns: List[str]) -> List[Dict[str, Union[str, int, float]]]:
    """
    Execute a SELECT query and return results as dictionaries

    Args:
        query (str): SQL query to execute
        columns (List[str]): List of column names

    Returns:
        List of dictionaries containing the query results
    """
    try:
      if not self._connect():
        return []
      
      cursor = self.connection.cursor(dictionary=True)
      cursor.execute(query)
      rows = cursor.fetchall()
      
      # If not using dictionary cursor (MySQL Connector < 2.0)
      if rows and not isinstance(rows[0], dict):
        rows = [dict(zip(columns, row)) for row in rows]
      
      self.logger.info(f"Query executed successfully: {query}")
      return rows
    
    except mysql.connector.Error as err:
      self.logger.error(f"Query error: {err}")
      return []
    finally:
      if cursor:
        cursor.close()
      self._disconnect()
      
      