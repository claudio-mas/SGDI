"""
System settings model
"""
from app import db
from datetime import datetime


class SystemSettings(db.Model):
    """
    System configuration settings stored in database.
    Uses key-value pairs for flexible configuration.
    """
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    chave = db.Column(db.String(100), unique=True, nullable=False, index=True)
    valor = db.Column(db.Text, nullable=True)
    descricao = db.Column(db.String(255), nullable=True)
    tipo = db.Column(db.String(20), nullable=False, default='string')  # string, int, bool, json
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SystemSettings {self.chave}={self.valor}>'
    
    def get_typed_value(self):
        """
        Get value converted to appropriate type.
        
        Returns:
            Value converted based on tipo field
        """
        if self.valor is None:
            return None
        
        if self.tipo == 'int':
            try:
                return int(self.valor)
            except (ValueError, TypeError):
                return 0
        elif self.tipo == 'bool':
            return self.valor.lower() in ('true', '1', 'yes', 'on')
        elif self.tipo == 'json':
            import json
            try:
                return json.loads(self.valor)
            except (ValueError, TypeError):
                return {}
        else:  # string
            return self.valor
    
    def set_typed_value(self, value):
        """
        Set value from typed input.
        
        Args:
            value: Value to set (will be converted to string)
        """
        if value is None:
            self.valor = None
        elif self.tipo == 'json':
            import json
            self.valor = json.dumps(value)
        else:
            self.valor = str(value)
