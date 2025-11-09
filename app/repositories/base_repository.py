"""
Base repository with generic CRUD operations
"""
from typing import TypeVar, Generic, Type, Optional, List, Dict, Any
from sqlalchemy.orm import Query
from sqlalchemy import desc, asc
from app import db

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """
    Generic base repository providing CRUD operations for all models.
    
    This class implements the Repository pattern to abstract data access logic
    and provide a consistent interface for database operations.
    """
    
    def __init__(self, model: Type[T]):
        """
        Initialize repository with a specific model class.
        
        Args:
            model: SQLAlchemy model class
        """
        self.model = model
        self.session = db.session
    
    def get_by_id(self, id: int) -> Optional[T]:
        """
        Retrieve a single record by its primary key.
        
        Args:
            id: Primary key value
            
        Returns:
            Model instance or None if not found
        """
        return self.session.query(self.model).get(id)
    
    def get_all(self) -> List[T]:
        """
        Retrieve all records.
        
        Returns:
            List of all model instances
        """
        return self.session.query(self.model).all()
    
    def filter_by(self, **kwargs) -> List[T]:
        """
        Filter records by specified criteria.
        
        Args:
            **kwargs: Field-value pairs for filtering
            
        Returns:
            List of matching model instances
        """
        return self.session.query(self.model).filter_by(**kwargs).all()
    
    def get_one_by(self, **kwargs) -> Optional[T]:
        """
        Get a single record matching the criteria.
        
        Args:
            **kwargs: Field-value pairs for filtering
            
        Returns:
            First matching model instance or None
        """
        return self.session.query(self.model).filter_by(**kwargs).first()
    
    def create(self, **kwargs) -> T:
        """
        Create a new record.
        
        Args:
            **kwargs: Field-value pairs for the new record
            
        Returns:
            Created model instance
        """
        instance = self.model(**kwargs)
        self.session.add(instance)
        self.session.commit()
        return instance
    
    def update(self, id: int, **kwargs) -> Optional[T]:
        """
        Update an existing record.
        
        Args:
            id: Primary key of record to update
            **kwargs: Field-value pairs to update
            
        Returns:
            Updated model instance or None if not found
        """
        instance = self.get_by_id(id)
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            self.session.commit()
        return instance
    
    def delete(self, id: int) -> bool:
        """
        Delete a record by its primary key.
        
        Args:
            id: Primary key of record to delete
            
        Returns:
            True if deleted, False if not found
        """
        instance = self.get_by_id(id)
        if instance:
            self.session.delete(instance)
            self.session.commit()
            return True
        return False
    
    def count(self, **kwargs) -> int:
        """
        Count records matching the criteria.
        
        Args:
            **kwargs: Field-value pairs for filtering
            
        Returns:
            Number of matching records
        """
        query = self.session.query(self.model)
        if kwargs:
            query = query.filter_by(**kwargs)
        return query.count()
    
    def exists(self, **kwargs) -> bool:
        """
        Check if any record exists matching the criteria.
        
        Args:
            **kwargs: Field-value pairs for filtering
            
        Returns:
            True if at least one record exists
        """
        return self.count(**kwargs) > 0
    
    def paginate(
        self,
        page: int = 1,
        per_page: int = 20,
        order_by: Optional[str] = None,
        order_dir: str = 'asc',
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Paginate query results with optional filtering and sorting.
        
        Args:
            page: Page number (1-indexed)
            per_page: Number of items per page
            order_by: Field name to sort by
            order_dir: Sort direction ('asc' or 'desc')
            filters: Dictionary of field-value pairs for filtering
            
        Returns:
            Dictionary containing:
                - items: List of model instances for current page
                - total: Total number of records
                - page: Current page number
                - per_page: Items per page
                - pages: Total number of pages
                - has_prev: Boolean indicating if previous page exists
                - has_next: Boolean indicating if next page exists
        """
        query = self.session.query(self.model)
        
        # Apply filters
        if filters:
            query = query.filter_by(**filters)
        
        # Apply sorting
        if order_by and hasattr(self.model, order_by):
            order_column = getattr(self.model, order_by)
            if order_dir.lower() == 'desc':
                query = query.order_by(desc(order_column))
            else:
                query = query.order_by(asc(order_column))
        
        # Get total count before pagination
        total = query.count()
        
        # Calculate pagination
        pages = (total + per_page - 1) // per_page  # Ceiling division
        page = max(1, min(page, pages)) if pages > 0 else 1
        
        # Apply pagination
        offset = (page - 1) * per_page
        items = query.limit(per_page).offset(offset).all()
        
        return {
            'items': items,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': pages,
            'has_prev': page > 1,
            'has_next': page < pages
        }
    
    def get_query(self) -> Query:
        """
        Get base query for the model.
        Useful for building complex queries in specialized repositories.
        
        Returns:
            SQLAlchemy Query object
        """
        return self.session.query(self.model)
    
    def bulk_create(self, items: List[Dict[str, Any]]) -> List[T]:
        """
        Create multiple records in a single transaction.
        
        Args:
            items: List of dictionaries with field-value pairs
            
        Returns:
            List of created model instances
        """
        instances = [self.model(**item) for item in items]
        self.session.bulk_save_objects(instances, return_defaults=True)
        self.session.commit()
        return instances
    
    def bulk_update(self, updates: List[Dict[str, Any]]) -> int:
        """
        Update multiple records in a single transaction.
        Each update dict must contain 'id' key.
        
        Args:
            updates: List of dictionaries with 'id' and field-value pairs
            
        Returns:
            Number of records updated
        """
        count = 0
        for update_data in updates:
            if 'id' in update_data:
                instance_id = update_data.pop('id')
                if self.update(instance_id, **update_data):
                    count += 1
        return count
    
    def bulk_delete(self, ids: List[int]) -> int:
        """
        Delete multiple records by their IDs.
        
        Args:
            ids: List of primary key values
            
        Returns:
            Number of records deleted
        """
        count = self.session.query(self.model).filter(
            self.model.id.in_(ids)
        ).delete(synchronize_session=False)
        self.session.commit()
        return count
