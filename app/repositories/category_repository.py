"""
Category repository with hierarchy traversal
"""
from typing import Optional, List, Dict, Any
from sqlalchemy import func
from app.repositories.base_repository import BaseRepository
from app.models.document import Categoria, Pasta


class CategoryRepository(BaseRepository[Categoria]):
    """
    Repository for Categoria model with hierarchical operations.
    Handles category tree traversal and hierarchy management.
    """
    
    def __init__(self):
        """Initialize CategoryRepository with Categoria model."""
        super().__init__(Categoria)
    
    def get_by_name(self, nome: str) -> Optional[Categoria]:
        """
        Get category by name.
        
        Args:
            nome: Category name
            
        Returns:
            Categoria instance or None
        """
        return self.get_one_by(nome=nome)
    
    def get_root_categories(self) -> List[Categoria]:
        """
        Get all top-level categories (no parent).
        
        Returns:
            List of root Categoria instances
        """
        return self.get_query().filter(
            Categoria.categoria_pai_id.is_(None),
            Categoria.ativo == True
        ).order_by(Categoria.ordem, Categoria.nome).all()
    
    def get_subcategories(self, categoria_id: int) -> List[Categoria]:
        """
        Get direct subcategories of a category.
        
        Args:
            categoria_id: Parent category ID
            
        Returns:
            List of child Categoria instances
        """
        return self.get_query().filter(
            Categoria.categoria_pai_id == categoria_id,
            Categoria.ativo == True
        ).order_by(Categoria.ordem, Categoria.nome).all()
    
    def get_hierarchy(self) -> List[Dict[str, Any]]:
        """
        Get complete category hierarchy as nested structure.
        
        Returns:
            List of category dicts with nested children
        """
        def build_tree(parent_id: Optional[int] = None) -> List[Dict[str, Any]]:
            """Recursively build category tree."""
            query = self.get_query().filter(Categoria.ativo == True)
            if parent_id is None:
                query = query.filter(Categoria.categoria_pai_id.is_(None))
            else:
                query = query.filter(Categoria.categoria_pai_id == parent_id)
            
            categories = query.order_by(Categoria.ordem, Categoria.nome).all()
            
            result = []
            for cat in categories:
                cat_dict = {
                    'id': cat.id,
                    'nome': cat.nome,
                    'descricao': cat.descricao,
                    'icone': cat.icone,
                    'cor': cat.cor,
                    'ordem': cat.ordem,
                    'children': build_tree(cat.id)
                }
                result.append(cat_dict)
            return result
        
        return build_tree()
    
    def get_all_descendants(self, categoria_id: int) -> List[Categoria]:
        """
        Get all descendant categories (recursive).
        
        Args:
            categoria_id: Parent category ID
            
        Returns:
            List of all descendant Categoria instances
        """
        descendants = []
        
        def collect_descendants(parent_id: int):
            """Recursively collect all descendants."""
            children = self.get_subcategories(parent_id)
            for child in children:
                descendants.append(child)
                collect_descendants(child.id)
        
        collect_descendants(categoria_id)
        return descendants
    
    def get_path_to_root(self, categoria_id: int) -> List[Categoria]:
        """
        Get path from category to root (breadcrumb).
        
        Args:
            categoria_id: Category ID
            
        Returns:
            List of Categoria instances from root to specified category
        """
        path = []
        current = self.get_by_id(categoria_id)
        
        while current:
            path.insert(0, current)
            if current.categoria_pai_id:
                current = self.get_by_id(current.categoria_pai_id)
            else:
                break
        
        return path
    
    def get_depth(self, categoria_id: int) -> int:
        """
        Get depth level of category in hierarchy (0 = root).
        
        Args:
            categoria_id: Category ID
            
        Returns:
            Depth level
        """
        depth = 0
        current = self.get_by_id(categoria_id)
        
        while current and current.categoria_pai_id:
            depth += 1
            current = self.get_by_id(current.categoria_pai_id)
        
        return depth
    
    def can_move_to_parent(self, categoria_id: int, new_parent_id: Optional[int]) -> bool:
        """
        Check if category can be moved to new parent (prevent circular references).
        
        Args:
            categoria_id: Category to move
            new_parent_id: New parent category ID (None for root)
            
        Returns:
            True if move is valid, False otherwise
        """
        if new_parent_id is None:
            return True
        
        if categoria_id == new_parent_id:
            return False
        
        # Check if new parent is a descendant of category (would create cycle)
        descendants = self.get_all_descendants(categoria_id)
        descendant_ids = [d.id for d in descendants]
        
        return new_parent_id not in descendant_ids
    
    def get_document_count(self, categoria_id: int, include_subcategories: bool = False) -> int:
        """
        Get number of documents in category.
        
        Args:
            categoria_id: Category ID
            include_subcategories: If True, count documents in subcategories too
            
        Returns:
            Document count
        """
        from app.models.document import Documento
        
        if include_subcategories:
            # Get all descendant category IDs
            descendants = self.get_all_descendants(categoria_id)
            category_ids = [categoria_id] + [d.id for d in descendants]
            
            count = self.session.query(func.count(Documento.id)).filter(
                Documento.categoria_id.in_(category_ids),
                Documento.status == 'ativo'
            ).scalar()
        else:
            count = self.session.query(func.count(Documento.id)).filter(
                Documento.categoria_id == categoria_id,
                Documento.status == 'ativo'
            ).scalar()
        
        return count or 0
    
    def get_active_categories(self) -> List[Categoria]:
        """
        Get all active categories.
        
        Returns:
            List of active Categoria instances
        """
        return self.filter_by(ativo=True)


class FolderRepository(BaseRepository[Pasta]):
    """
    Repository for Pasta (Folder) model with hierarchical operations.
    """
    
    def __init__(self):
        """Initialize FolderRepository with Pasta model."""
        super().__init__(Pasta)
    
    def get_root_folders(self, usuario_id: int) -> List[Pasta]:
        """
        Get all top-level folders for a user.
        
        Args:
            usuario_id: User ID
            
        Returns:
            List of root Pasta instances
        """
        return self.get_query().filter(
            Pasta.pasta_pai_id.is_(None),
            Pasta.usuario_id == usuario_id
        ).order_by(Pasta.ordem, Pasta.nome).all()
    
    def get_subfolders(self, pasta_id: int) -> List[Pasta]:
        """
        Get direct subfolders of a folder.
        
        Args:
            pasta_id: Parent folder ID
            
        Returns:
            List of child Pasta instances
        """
        return self.get_query().filter(
            Pasta.pasta_pai_id == pasta_id
        ).order_by(Pasta.ordem, Pasta.nome).all()
    
    def get_user_folders(self, usuario_id: int) -> List[Pasta]:
        """
        Get all folders owned by a user.
        
        Args:
            usuario_id: User ID
            
        Returns:
            List of Pasta instances
        """
        return self.filter_by(usuario_id=usuario_id)
    
    def get_hierarchy(self, usuario_id: int) -> List[Dict[str, Any]]:
        """
        Get complete folder hierarchy for a user.
        
        Args:
            usuario_id: User ID
            
        Returns:
            List of folder dicts with nested children
        """
        def build_tree(parent_id: Optional[int] = None) -> List[Dict[str, Any]]:
            """Recursively build folder tree."""
            query = self.get_query().filter(Pasta.usuario_id == usuario_id)
            if parent_id is None:
                query = query.filter(Pasta.pasta_pai_id.is_(None))
            else:
                query = query.filter(Pasta.pasta_pai_id == parent_id)
            
            folders = query.order_by(Pasta.ordem, Pasta.nome).all()
            
            result = []
            for folder in folders:
                folder_dict = {
                    'id': folder.id,
                    'nome': folder.nome,
                    'descricao': folder.descricao,
                    'cor': folder.cor,
                    'ordem': folder.ordem,
                    'nivel': folder.nivel,
                    'children': build_tree(folder.id)
                }
                result.append(folder_dict)
            return result
        
        return build_tree()
    
    def get_path_to_root(self, pasta_id: int) -> List[Pasta]:
        """
        Get path from folder to root (breadcrumb).
        
        Args:
            pasta_id: Folder ID
            
        Returns:
            List of Pasta instances from root to specified folder
        """
        path = []
        current = self.get_by_id(pasta_id)
        
        while current:
            path.insert(0, current)
            if current.pasta_pai_id:
                current = self.get_by_id(current.pasta_pai_id)
            else:
                break
        
        return path
    
    def can_move_to_parent(self, pasta_id: int, new_parent_id: Optional[int], max_depth: int = 5) -> bool:
        """
        Check if folder can be moved to new parent.
        
        Args:
            pasta_id: Folder to move
            new_parent_id: New parent folder ID (None for root)
            max_depth: Maximum allowed depth
            
        Returns:
            True if move is valid, False otherwise
        """
        if new_parent_id is None:
            return True
        
        if pasta_id == new_parent_id:
            return False
        
        # Check depth limit
        new_parent = self.get_by_id(new_parent_id)
        if new_parent and new_parent.nivel >= max_depth - 1:
            return False
        
        # Check if new parent is a descendant (would create cycle)
        current = new_parent
        while current:
            if current.id == pasta_id:
                return False
            if current.pasta_pai_id:
                current = self.get_by_id(current.pasta_pai_id)
            else:
                break
        
        return True
    
    def get_document_count(self, pasta_id: int) -> int:
        """
        Get number of documents in folder.
        
        Args:
            pasta_id: Folder ID
            
        Returns:
            Document count
        """
        from app.models.document import Documento
        
        count = self.session.query(func.count(Documento.id)).filter(
            Documento.pasta_id == pasta_id,
            Documento.status == 'ativo'
        ).scalar()
        
        return count or 0
