from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.sql import text

from src.utils import get_db

router = APIRouter()


class KeySearchParam(BaseModel):
    include: list[str] = ["高抗A相", "油色谱"]
    exclude: list[str] = []


@router.post("/keys")
async def get_keys_by_keywords(param: KeySearchParam, db=Depends(get_db)):
    include = param.include
    exclude = param.exclude

    if include:
        include_conditions = [f"path LIKE '%{i}%'" for i in include]
        where_clause = f"WHERE {' AND '.join(include_conditions)}"
    else:
        where_clause = ""

    if exclude:
        exclude_conditions = [f"path NOT LIKE '%{e}%'" for e in exclude]
        where_clause += (
            f" AND {' AND '.join(exclude_conditions)}"
            if where_clause
            else f"WHERE {' AND '.join(exclude_conditions)}"
        )

    statement = f"""
    SELECT *
    FROM analog
    {where_clause}
    """
    results = db.execute(text(statement)).fetchall()
    results = [r._asdict() for r in results]
    return {
        "code": 200,
        "message": "success",
        "data": results,
    }


class RealtimeDataSearchParam(BaseModel):
    keys: list[str] = ["4222125144473606", "4222125148602374"]


@router.post("/realtime")
async def get_realtime_data(keys: RealtimeDataSearchParam, db=Depends(get_db)):
    if not keys.keys:
        raise HTTPException(status_code=400, detail="keys is empty")

    statement = f"""
    SELECT *
    FROM analog
    WHERE scadaid IN ({','.join(keys.keys)})
    """
    results = db.execute(text(statement)).fetchall()
    results = [r._asdict() for r in results]
    return {
        "code": 200,
        "message": "success",
        "data": results,
    }


current_data_index = 0


@router.post("/realtime/mock")
async def get_mock_realtime_data(keys: RealtimeDataSearchParam, db=Depends(get_db)):
    if not keys.keys:
        raise HTTPException(status_code=400, detail="keys is empty")

    # all tables start with "scada_analogueother" in the database
    statement = """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
    AND table_name LIKE 'scada_analogueother%'
    """
    results = db.execute(text(statement)).fetchall()
    tables = [r[0] for r in results]

    results = []
    for key in keys.keys:
        # count the number of data in all tables
        statement = f"""
        { ' UNION ALL '.join([f"SELECT COUNT(*) FROM {table} WHERE attr_oid = {key}" for table in tables]) }
        """
        results = db.execute(text(statement)).fetchall()
        counts = [r[0] for r in results]
        tables_exist_data = [table for table, count in zip(tables, counts) if count > 0]
        total = sum(counts)

        # get the current data
        global current_data_index
        current_data_index += 1
        current_data_index %= total
        statement = f"""
        { ' UNION ALL '.join([f"SELECT * FROM {table} WHERE attr_oid = {key}" for table in tables_exist_data]) }
        LIMIT 1 OFFSET {current_data_index}
        """
        results = db.execute(text(statement)).fetchall()
        results = [r._asdict() for r in results]

        results.append(results[0])
    return {
        "code": 200,
        "message": "success",
        "data": results,
    }
