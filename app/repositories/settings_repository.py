"""
System settings repository
"""
from typing import Optional, Dict, Any
from app.repositories.base_repository import BaseRepository
from app.models.settings import SystemSettings


class SettingsRepository(BaseRepository[SystemSettings]):
    """
    Repository for SystemSettings model.
    Provides key-value storage for system configuration.
    """
    
    def __init__(self):
        """Initialize SettingsRepository with SystemSettings model."""
        super().__init__(SystemSettings)
    
    def get_by_key(self, chave: str) -> Optional[SystemSettings]:
        """
        Get setting by key.
        
        Args:
            chave: Setting key
            
        Returns:
            SystemSettings instance or None
        """
        return self.get_one_by(chave=chave)
    
    def get_value(self, chave: str, default: Any = None) -> Any:
        """
        Get setting value by key with type conversion.
        
        Args:
            chave: Setting key
            default: Default value if not found
            
        Returns:
            Setting value converted to appropriate type, or default
        """
        setting = self.get_by_key(chave)
        if setting:
            return setting.get_typed_value()
        return default
    
    def set_value(
        self,
        chave: str,
        valor: Any,
        descricao: Optional[str] = None,
        tipo: str = 'string'
    ) -> SystemSettings:
        """
        Set or update a setting value.
        
        Args:
            chave: Setting key
            valor: Setting value
            descricao: Optional description
            tipo: Value type (string, int, bool, json)
            
        Returns:
            SystemSettings instance
        """
        setting = self.get_by_key(chave)
        
        if setting:
            # Update existing
            setting.set_typed_value(valor)
            if descricao:
                setting.descricao = descricao
            self.session.commit()
        else:
            # Create new
            setting = SystemSettings(
                chave=chave,
                descricao=descricao,
                tipo=tipo
            )
            setting.set_typed_value(valor)
            self.session.add(setting)
            self.session.commit()
        
        return setting
    
    def get_all_settings(self) -> Dict[str, Any]:
        """
        Get all settings as a dictionary.
        
        Returns:
            Dictionary of key-value pairs with typed values
        """
        settings = self.get_all()
        return {s.chave: s.get_typed_value() for s in settings}
    
    def initialize_defaults(self):
        """Initialize default system settings if they don't exist."""
        defaults = [
            ('max_file_size_mb', '50', 'Tamanho máximo de arquivo em MB', 'int'),
            ('allowed_extensions', 'pdf,doc,docx,xls,xlsx,jpg,png,tif', 'Extensões de arquivo permitidas', 'string'),
            ('trash_retention_days', '30', 'Dias de retenção na lixeira', 'int'),
            ('max_versions_per_document', '10', 'Máximo de versões por documento', 'int'),
            ('session_timeout_minutes', '60', 'Timeout de sessão em minutos', 'int'),
            ('system_logo', '', 'Caminho do logo do sistema', 'string'),
        ]
        
        for chave, valor, descricao, tipo in defaults:
            if not self.get_by_key(chave):
                self.set_value(chave, valor, descricao, tipo)
