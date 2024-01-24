from sqlalchemy.dialects.mysql import BIGINT, DATETIME, INTEGER, LONGTEXT, TIME
from sqlalchemy import Boolean, Column, Integer, String, VARCHAR
from typing import List, Optional
from sqlmodel import (
    Field,
    Relationship,
    Session,
    SQLModel,
    create_engine,
    select,
)
from database import Base


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
    child_id: int = Field(primary_key=True, nullable=False,foreign_key="child.id")
    #child_id: int = Field(primary_key=True, nullable=False)
    desc: Optional[str] = Field(default=None)
    #child: Optional[ChildTable] = Relationship()


class ParentTable(SQLModel, table=True):
    __tablename__ = 'parent_table'

    id: int = Field( primary_key=True)
    desc: Optional[str] = Field(default=None)
    #child_table: list = []
    #child_table: List["ChildTable"] = Relationship(back_populates="parent_table")

 #-----------------------------------------------------------------

class TeamBase(SQLModel):
    name: str = Field(default=None,index=True)
    headquaters: str = Field(default=None,alias="kantor pusat")
    team_name: str
    description: str

    # class Config:
    #     populate_by_name = True


class Team(TeamBase, table=True):
    __tablename__ = 'team'
    id: Optional[int] = Field(default=None, primary_key=True)

    heroes: List["Hero"] = Relationship(back_populates="team")

class TeamRead(TeamBase):
    id: int

#-----------------------------------------------------------

# class Hero(SQLModel, table=True):
#     __tablename__ = 'hero'
#     id: Optional[int] = Field(default=None, primary_key=True)
#     name: str = Field(index=True)
#     secret_name: str
#     age: Optional[int] = Field(default=None, index=True)

#     team_id: Optional[int] = Field(default=None, foreign_key="team.id")
#     team: Optional[Team] = Relationship(back_populates="heroes")


class HeroBase(SQLModel):
    name: str = Field(index=True)
    secret_name: str
    age: Optional[int] = Field(default=None, index=True)
    team_id: Optional[int] = Field(default=None, foreign_key="team.id")


class Hero(HeroBase, table=True):
    __tablename__ = 'hero'
    id: Optional[int] = Field(default=None, primary_key=True)
    team: Optional[Team] = Relationship(back_populates="heroes")

class HeroRead(HeroBase):
    id: int

class HeroReadWithTeam(HeroRead):
    team: Optional[TeamRead] = None


class TeamReadWithHeroes(TeamRead):
    heroes: List[HeroRead] = []
