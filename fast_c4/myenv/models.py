from sqlalchemy.dialects.mysql import BIGINT, DATETIME, INTEGER, LONGTEXT, TIME
from typing import List, Optional
from sqlmodel import Field, Relationship, SQLModel


class ChildTable(SQLModel,table=True):
    __tablename__ = 'child_table'

    id: int = Field(primary_key=True, nullable=False)
    parent_id: int = Field(default= None, foreign_key= 'parent_table.id')
    #parent_id: int = Field(primary_key=True, nullable=False)
    desc: Optional[str] 
    #grandchilds: list[GrandchildTable]
    #parent: Optional["ParentTable"] = Relationship(back_populates="child_table_ibfk_1")
    

class GrandchildTable(SQLModel, table=True):
    __tablename__ = 'grandchild_table'

    id: int = Field(primary_key=True, nullable=False)
    #child_id: int = Field(primary_key=True, nullable=False,foreign_key="child.id")
    child_id: int = Field(primary_key=True, nullable=False)
    desc: Optional[str] = Field(default=None)
    #child: Optional[ChildTable] = Relationship()


class ParentTable(SQLModel, table=True):
    __tablename__ = 'parent_table'

    id: int = Field( primary_key=True)
    desc: Optional[str] = Field(default=None)
    #child_table: list = []
    #child_table: List["ChildTable"] = Relationship(back_populates="parent_table")

    

