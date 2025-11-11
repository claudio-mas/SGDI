"""
Category and folder service for business logic
"""
from typing import Optional, List, Dict, Any
from flask import current_app
from app import db
from app.models.document import Categoria, Pasta
from app.repositories.category_repository import CategoryRepository, FolderRepository
from app.services.audit_service import AuditService


class CategoryService:
    """Service for category management operations"""
    
    def __init__(self):
        """Initialize CategoryService"""
        self.category_repo = CategoryRepository()
        self.audit_service = AuditService()
    
    def get_all_categories(self) -> List[Categoria]:
        """Get all active categories"""
        return self.category_repo.get_active_categories()
    
    def get_category_hierarchy(self) -> List[Dict[str, Any]]:
        """Get category hierarchy as nested structure"""
        return self.category_repo.get_hierarchy()
    
    def get_category_by_id(self, categoria_id: int) -> Optional[Categoria]:
        """Get category by ID"""
        return self.category_repo.get_by_id(categoria_id)
    
    def create_category(self, data: Dict[str, Any], user_id: int) -> Categoria:
        """
        Create a new category.
        
        Args:
            data: Category data
            user_id: User creating the category
            
        Returns:
            Created Categoria instance
        """
        # Create category
        categoria = self.category_repo.create(
            nome=data['nome'],
            descricao=data.get('descricao'),
            categoria_pai_id=data.get('categoria_pai_id') or None,
            icone=data.get('icone'),
            cor=data.get('cor', '#007bff'),
            ordem=data.get('ordem', 0),
            ativo=True
        )
        
        # Log action
        self.audit_service.log_action(
            usuario_id=user_id,
            acao='create_category',
            tabela='categorias',
            registro_id=categoria.id,
            dados={'nome': categoria.nome}
        )
        
        current_app.logger.info(f"Category created: {categoria.nome} by user {user_id}")
        return categoria
    
    def update_category(self, categoria_id: int, data: Dict[str, Any], user_id: int) -> Categoria:
        """
        Update category.
        
        Args:
            categoria_id: Category ID
            data: Updated category data
            user_id: User updating the category
            
        Returns:
            Updated Categoria instance
        """
        categoria = self.category_repo.get_by_id(categoria_id)
        if not categoria:
            raise ValueError('Categoria não encontrada')
        
        # Store old values for audit
        old_data = {
            'nome': categoria.nome,
            'categoria_pai_id': categoria.categoria_pai_id
        }
        
        # Update fields
        categoria.nome = data['nome']
        categoria.descricao = data.get('descricao')
        categoria.icone = data.get('icone')
        categoria.cor = data.get('cor', '#007bff')
        categoria.ordem = data.get('ordem', 0)
        
        # Validate parent change
        new_parent_id = data.get('categoria_pai_id') or None
        if new_parent_id != categoria.categoria_pai_id:
            if new_parent_id and not self.category_repo.can_move_to_parent(categoria_id, new_parent_id):
                raise ValueError('Não é possível mover a categoria para este pai (referência circular ou limite de profundidade)')
            categoria.categoria_pai_id = new_parent_id
        
        # Save changes
        self.category_repo.save(categoria)
        
        # Log action
        self.audit_service.log_action(
            usuario_id=user_id,
            acao='update_category',
            tabela='categorias',
            registro_id=categoria.id,
            dados={'old': old_data, 'new': {'nome': categoria.nome, 'categoria_pai_id': categoria.categoria_pai_id}}
        )
        
        current_app.logger.info(f"Category updated: {categoria.nome} by user {user_id}")
        return categoria
    
    def delete_category(self, categoria_id: int, user_id: int) -> bool:
        """
        Delete (deactivate) category.
        
        Args:
            categoria_id: Category ID
            user_id: User deleting the category
            
        Returns:
            True if successful
        """
        categoria = self.category_repo.get_by_id(categoria_id)
        if not categoria:
            raise ValueError('Categoria não encontrada')
        
        # Check if category has documents
        doc_count = self.category_repo.get_document_count(categoria_id, include_subcategories=True)
        if doc_count > 0:
            raise ValueError(f'Não é possível excluir categoria com {doc_count} documento(s) associado(s)')
        
        # Deactivate category
        categoria.ativo = False
        self.category_repo.save(categoria)
        
        # Log action
        self.audit_service.log_action(
            usuario_id=user_id,
            acao='delete_category',
            tabela='categorias',
            registro_id=categoria.id,
            dados={'nome': categoria.nome}
        )
        
        current_app.logger.info(f"Category deleted: {categoria.nome} by user {user_id}")
        return True
    
    def get_category_stats(self, categoria_id: int) -> Dict[str, Any]:
        """
        Get category statistics.
        
        Args:
            categoria_id: Category ID
            
        Returns:
            Dictionary with statistics
        """
        categoria = self.category_repo.get_by_id(categoria_id)
        if not categoria:
            raise ValueError('Categoria não encontrada')
        
        doc_count = self.category_repo.get_document_count(categoria_id, include_subcategories=False)
        doc_count_total = self.category_repo.get_document_count(categoria_id, include_subcategories=True)
        subcategories = self.category_repo.get_subcategories(categoria_id)
        
        return {
            'categoria': categoria,
            'document_count': doc_count,
            'document_count_total': doc_count_total,
            'subcategory_count': len(subcategories),
            'subcategories': subcategories
        }


class FolderService:
    """Service for folder management operations"""
    
    def __init__(self):
        """Initialize FolderService"""
        self.folder_repo = FolderRepository()
        self.audit_service = AuditService()
    
    def get_user_folders(self, usuario_id: int) -> List[Pasta]:
        """Get all folders for a user"""
        return self.folder_repo.get_user_folders(usuario_id)
    
    def get_folder_hierarchy(self, usuario_id: int) -> List[Dict[str, Any]]:
        """Get folder hierarchy for a user"""
        return self.folder_repo.get_hierarchy(usuario_id)
    
    def get_folder_by_id(self, pasta_id: int) -> Optional[Pasta]:
        """Get folder by ID"""
        return self.folder_repo.get_by_id(pasta_id)
    
    def create_folder(self, data: Dict[str, Any], usuario_id: int) -> Pasta:
        """
        Create a new folder.
        
        Args:
            data: Folder data
            usuario_id: User creating the folder
            
        Returns:
            Created Pasta instance
        """
        # Validate depth limit
        pasta_pai_id = data.get('pasta_pai_id') or None
        if pasta_pai_id:
            parent = self.folder_repo.get_by_id(pasta_pai_id)
            if parent and parent.nivel >= 4:  # Max depth is 5 (0-4)
                raise ValueError('Limite de profundidade atingido (máximo 5 níveis)')
            
            # Verify ownership
            if parent.usuario_id != usuario_id:
                raise ValueError('Você não tem permissão para criar subpastas nesta pasta')
        
        # Create folder
        pasta = self.folder_repo.create(
            nome=data['nome'],
            descricao=data.get('descricao'),
            pasta_pai_id=pasta_pai_id,
            usuario_id=usuario_id,
            cor=data.get('cor', '#ffc107'),
            ordem=data.get('ordem', 0)
        )
        
        # Log action
        self.audit_service.log_action(
            usuario_id=usuario_id,
            acao='create_folder',
            tabela='pastas',
            registro_id=pasta.id,
            dados={'nome': pasta.nome}
        )
        
        current_app.logger.info(f"Folder created: {pasta.nome} by user {usuario_id}")
        return pasta
    
    def update_folder(self, pasta_id: int, data: Dict[str, Any], usuario_id: int) -> Pasta:
        """
        Update folder.
        
        Args:
            pasta_id: Folder ID
            data: Updated folder data
            usuario_id: User updating the folder
            
        Returns:
            Updated Pasta instance
        """
        pasta = self.folder_repo.get_by_id(pasta_id)
        if not pasta:
            raise ValueError('Pasta não encontrada')
        
        # Verify ownership
        if pasta.usuario_id != usuario_id:
            raise ValueError('Você não tem permissão para editar esta pasta')
        
        # Store old values for audit
        old_data = {
            'nome': pasta.nome,
            'pasta_pai_id': pasta.pasta_pai_id
        }
        
        # Update fields
        pasta.nome = data['nome']
        pasta.descricao = data.get('descricao')
        pasta.cor = data.get('cor', '#ffc107')
        pasta.ordem = data.get('ordem', 0)
        
        # Validate parent change
        new_parent_id = data.get('pasta_pai_id') or None
        if new_parent_id != pasta.pasta_pai_id:
            if new_parent_id and not self.folder_repo.can_move_to_parent(pasta_id, new_parent_id):
                raise ValueError('Não é possível mover a pasta para este pai (referência circular ou limite de profundidade)')
            
            # Verify parent ownership
            if new_parent_id:
                parent = self.folder_repo.get_by_id(new_parent_id)
                if parent.usuario_id != usuario_id:
                    raise ValueError('Você não tem permissão para mover para esta pasta')
            
            pasta.pasta_pai_id = new_parent_id
        
        # Save changes
        self.folder_repo.save(pasta)
        
        # Log action
        self.audit_service.log_action(
            usuario_id=usuario_id,
            acao='update_folder',
            tabela='pastas',
            registro_id=pasta.id,
            dados={'old': old_data, 'new': {'nome': pasta.nome, 'pasta_pai_id': pasta.pasta_pai_id}}
        )
        
        current_app.logger.info(f"Folder updated: {pasta.nome} by user {usuario_id}")
        return pasta
    
    def delete_folder(self, pasta_id: int, usuario_id: int) -> bool:
        """
        Delete folder.
        
        Args:
            pasta_id: Folder ID
            usuario_id: User deleting the folder
            
        Returns:
            True if successful
        """
        pasta = self.folder_repo.get_by_id(pasta_id)
        if not pasta:
            raise ValueError('Pasta não encontrada')
        
        # Verify ownership
        if pasta.usuario_id != usuario_id:
            raise ValueError('Você não tem permissão para excluir esta pasta')
        
        # Check if folder has documents
        doc_count = self.folder_repo.get_document_count(pasta_id)
        if doc_count > 0:
            raise ValueError(f'Não é possível excluir pasta com {doc_count} documento(s)')
        
        # Check if folder has subfolders
        subfolders = self.folder_repo.get_subfolders(pasta_id)
        if subfolders:
            raise ValueError(f'Não é possível excluir pasta com {len(subfolders)} subpasta(s)')
        
        # Store folder name for logging (before deletion)
        pasta_nome = pasta.nome
        
        # Delete folder
        self.folder_repo.delete(pasta_id)
        
        # Log action
        self.audit_service.log_action(
            usuario_id=usuario_id,
            acao='delete_folder',
            tabela='pastas',
            registro_id=pasta_id,
            dados={'nome': pasta_nome}
        )
        
        current_app.logger.info(f"Folder deleted: {pasta_nome} by user {usuario_id}")
        return True
    
    def get_folder_breadcrumb(self, pasta_id: int) -> List[Pasta]:
        """Get breadcrumb path for folder"""
        return self.folder_repo.get_path_to_root(pasta_id)
    
    def get_folder_stats(self, pasta_id: int) -> Dict[str, Any]:
        """
        Get folder statistics.
        
        Args:
            pasta_id: Folder ID
            
        Returns:
            Dictionary with statistics
        """
        pasta = self.folder_repo.get_by_id(pasta_id)
        if not pasta:
            raise ValueError('Pasta não encontrada')
        
        doc_count = self.folder_repo.get_document_count(pasta_id)
        subfolders = self.folder_repo.get_subfolders(pasta_id)
        
        return {
            'pasta': pasta,
            'document_count': doc_count,
            'subfolder_count': len(subfolders),
            'subfolders': subfolders
        }
