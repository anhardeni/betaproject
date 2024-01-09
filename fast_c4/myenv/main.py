from fastapi import FastAPI, status
from fastapi.exceptions import HTTPException
from typing import Optional, List, Union
from models import *
from database import engine
from sqlmodel import Session, select


def get_session():
    with Session(engine) as session:
        yield session



app = FastAPI()

session=Session(bind=engine)


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q}


@app.get('/grandchilds', response_model=List[GrandchildTable],
         status_code=status.HTTP_200_OK)
async def get_all_grandchilds():
    statement = select(GrandchildTable)
    results = session.exec(statement).all()

    return results

@app.get('/childs', response_model=List[ChildTable],
         status_code=status.HTTP_200_OK)
async def get_all_childs():
    statement = select(ChildTable)
    results = session.exec(statement).all()

    return results


@app.get('/parents', response_model=List[ParentTable],
         status_code=status.HTTP_200_OK)
async def get_all_parents():
    statement = select(ParentTable)
    results = session.exec(statement).all()

    return results



@app.get('/child-parent', status_code=status.HTTP_200_OK)
async def get_all_childs_parents():
    statement = select(ChildTable,ParentTable).where(ChildTable.parent_id == ParentTable.id)
    results = session.exec(statement)
    res =[]
    for childs, parents in results:
        res.append( {"childs": childs , "parents": parents})
    return res


@app.get('/child-parent{id}', status_code=status.HTTP_200_OK)
async def get_all_childs_parents_id(id: int):
    statement = select(ChildTable,ParentTable).where(ChildTable.parent_id == ParentTable.id)
    statement = statement.where(ChildTable.id == id)
    results = session.exec(statement)
    res =[]
    for childs, parents in results:
        res.append( {"childs": childs , "parents": parents})
    return res


@app.get('/parent-child{id}', status_code=status.HTTP_200_OK)
async def get_all_parents_child_id(id: int):
    statement = select(ParentTable, ChildTable).where(ParentTable.id == ChildTable.parent_id)
    statement = statement.where(ParentTable.id == id)
    results = session.exec(statement)
    res =[]
    #res1=[]
    #for parents  in results:
        #res.append( {"parents": parents })
        #for childs in results:
        #    res1.append( {"childs": childs })
        #return res
    #return res

    for parents, childs in results:
        res.append( {"parents": parents , "childs": childs ,})
    return res



#if __name__ == "__main__":
    #uvicorn.run("main:app", host="localhost", port=8003, reload=True)
    #main()
