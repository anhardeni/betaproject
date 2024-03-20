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


class ParentBase(SQLModel):
     #desc: Optional[str] = Field(default=None)
     desc: Optional[str] = Field(validation_alias="descParent", default=None)
     #secret_name: str = Field(validation_alias="secretName")

class ParentTable(ParentBase, table=True):
    __tablename__ = 'parent_table'

    id: Optional [int]  = Field( primary_key=True)
    childs: List["ChildTable"] = Relationship(back_populates="parents")

class ParentRead(ParentBase):
    id: int 

# #-----------------------------------------------
class ChildBase(SQLModel):
    parent_id: Optional [int] = Field(default= None, foreign_key= 'parent_table.id')
    desc: Optional[str] = Field(default=None, validation_alias='Keterangan')
    

class ChildTable(ChildBase,table=True):
    __tablename__ = 'child_table'
    id: Optional [int] = Field(primary_key=True)
    parents: Optional["ParentTable"] = Relationship(back_populates="childs")
    grandchilds: List["GrandchildTable"] = Relationship(back_populates="childtables")
    
class ChildRead(ChildBase):
    id: int 
    grandchilds: List["GrandchildTable"] = []
    
#----------------------
class GrandchildBase(SQLModel):
    child_id: int = Field(default= None,foreign_key= 'child_table.id')
    desc: Optional[str] = Field(default=None)
   
class GrandchildTable(GrandchildBase, table=True):
    __tablename__ = 'grandchild_table'
    id: Optional [int] = Field(primary_key=True, nullable=False)
    childtables: Optional["ChildTable"] = Relationship(back_populates="grandchilds")

  
class GrandchildRead(GrandchildBase):
      id: int 
   

#-----------------------------------------------------------------
class ParentdWithChild(ParentRead):
    childs: List[ChildRead] = []
    #grandchilds: List[ChildWithGrandchild] = []


class ChildWithGrandchild(ChildRead):
    grandchilds: List[GrandchildRead] = []
   
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
