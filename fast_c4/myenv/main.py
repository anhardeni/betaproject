from fastapi import FastAPI, status, Depends, Query
from fastapi.exceptions import HTTPException
from typing import Optional, List, Union
from models import *
from database import engine, SessionLocal
from sqlmodel import Session, select

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlmodel import Field, Relationship, Session, SQLModel, create_engine, select
#from sqlalchemy.orm import Session


def get_session():
    with Session(engine) as session:
        yield session


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


def get_session():
    try:
        with Session(engine) as session:
            yield session
    finally:
        session.close()
    



app = FastAPI()

session=Session(bind=engine)


@app.get("/")
def read_root():
    return {"Hello": "World"}

# app.get("/loginc40") url 
# def read_root():
#     return {"Hello": "World"} username :password -> token



@app.get("/read_all")
async def read_all(db: Session = Depends(get_db)):
   return db.query(models.ParentsTable).all()


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


# @app.get('/grandchilds', response_model=List[GrandchildTable],
#          status_code=status.HTTP_200_OK)
# async def get_all_grandchilds():
#     statement = select(GrandchildTable)
#     results = session.exec(statement).all()

#     return results

# @app.get('/childs', response_model=List[ChildTable],
#          status_code=status.HTTP_200_OK)
# async def get_all_childs():
#     statement = select(ChildTable)
#     results = session.exec(statement).all()

#     return results


@app.get('/parents', response_model=List[ParentTable],
         status_code=status.HTTP_200_OK)
async def get_all_parents():
    statement = select(ParentTable)
    results = session.exec(statement).all()

    return results



# @app.get('/child-parent', status_code=status.HTTP_200_OK)
# async def get_all_childs_parents():
#     statement = select(ChildTable,ParentTable).where(ChildTable.parent_id == ParentTable.id)
#     results = session.exec(statement)
#     res =[]
#     for childs, parents in results:
#         res.append( {"childs": childs , "parents": parents})
#     return res


# @app.get('/child-parent{id}', status_code=status.HTTP_200_OK)
# async def get_all_childs_parents_id(id: int):
#     statement = select(ChildTable,ParentTable).where(ChildTable.parent_id == ParentTable.id)
#     statement = statement.where(ChildTable.id == id)
#     results = session.exec(statement)
#     res =[]
#     for childs, parents in results:
#         res.append( {"childs": childs , "parents": parents})
#     return res


# @app.get('/parent-child{id}', status_code=status.HTTP_200_OK)
# async def get_all_parents_child_id(id: int):
#     statement = select(ParentTable, ChildTable).where(ParentTable.id == ChildTable.parent_id)
#     statement = statement.where(ParentTable.id == id)
#     results = session.exec(statement)
#     res =[]
    
#     for parents, childs in results:
#         res.append( {"parents": parents , "childs": childs ,})
#     return res

@app.get("/parents-with-child/{id}", response_model=ParentdWithChild)
def read_parentwithchildren(*, id: int, session: Session = Depends(get_session)):
    parents = session.get(ParentTable, id)
    if not parents:
        raise HTTPException(status_code=404, detail="Parents not found")
    return parents



@app.get("/children-with-grandchild/{id}", response_model=ChildWithGrandchild)
def read_childwithgrandchild(*, id: int, session: Session = Depends(get_session)):
    child_table_link = session.get(ChildTable, id)
    if not  child_table_link:
        raise HTTPException(status_code=404, detail=" childs not found")
    return  child_table_link



@app.get('/hero', response_model=List[Hero],
         status_code=status.HTTP_200_OK)
async def get_all_heroes():
    statement = select(Hero)
    results = session.exec(statement).all()

    return results

@app.get('/hero/{name}', response_model=List[Hero],
         status_code=status.HTTP_200_OK)
async def get_one_hero(name: str):
    statement = select(Hero).where(Hero.name == name)
    results = session.exec(statement).all()

    return results

@app.get("/heroes/", response_model=List[HeroRead])
def read_heroes(
    *,
    session: Session = Depends(get_session),
    offset: int = 0,
    limit: int = Query(default=100, le=100),
):
    heroes = session.exec(select(Hero).offset(offset).limit(limit)).all()
    return heroes

# @app.get("/heroes/{hero_id}", response_model=HeroRead)
# def read_hero(*, session: Session = Depends(get_session), hero_id: int):
#     hero = session.get(Hero, hero_id)
#     if not hero:
#         raise HTTPException(status_code=404, detail="Hero not found")
#     return hero

# @app.get("/heroes/{hero_id}", response_model=HeroReadWithTeam)
# def read_hero(*, session: Session = Depends(get_session), hero_id: int):
#     hero = session.get(Hero, hero_id)
#     if not hero:
#         raise HTTPException(status_code=404, detail="Hero not found")
#     return hero

@app.get("/heroes/{id}", response_model=HeroReadWithTeam)
def read_hero(*, session: Session = Depends(get_session), id: int):
    hero = session.get(Hero, id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero


@app.get("/teams/{team_id}", response_model=TeamReadWithHeroes)
def read_team(*, team_id: int, session: Session = Depends(get_session)):
    team = session.get(Team, team_id)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team



#if __name__ == "__main__":
    #uvicorn.run("main:app", host="localhost", port=8003, reload=True)
    #main()
