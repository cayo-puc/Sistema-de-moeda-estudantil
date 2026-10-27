"""
Contrato Genérico do Padrão DAO (Data Access Object) — Lab03S02.
Isola a lógica de negócio e os controladores MVC dos detalhes de persistência relacional
(cumprindo a interface `IPersistência` do Diagrama de Componentes).
"""

from abc import ABC, abstractmethod
from typing import Generic, List, Optional, TypeVar

from src.config.database import DatabaseManager

T = TypeVar("T")


class GenericDAO(ABC, Generic[T]):
    """Interface base parametrizada para todos os DAOs do sistema."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    @abstractmethod
    def criar(self, entidade: T) -> T:
        """Persiste uma nova entidade no banco de dados de forma transacional."""
        raise NotImplementedError

    @abstractmethod
    def buscar_por_id(self, id_entidade: str) -> Optional[T]:
        """Recupera uma entidade pelo seu identificador único (UUID)."""
        raise NotImplementedError

    @abstractmethod
    def listar_todos(self) -> List[T]:
        """Retorna todas as entidades cadastradas."""
        raise NotImplementedError

    @abstractmethod
    def atualizar(self, entidade: T) -> Optional[T]:
        """Atualiza os atributos persistidos de uma entidade existente."""
        raise NotImplementedError

    @abstractmethod
    def remover(self, id_entidade: str) -> bool:
        """Remove a entidade do banco de dados pelo ID."""
        raise NotImplementedError

