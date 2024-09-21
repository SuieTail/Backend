from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session

from DB import utils, users, ais, rags
from Schema import base_schemas, ai_schemas
from AI import crud
from Blockchain import suiapi

import random


router = APIRouter()

@router.get("/", response_model=ai_schemas.AIReadList)
def get_ais(
    offset: int = Query(0, description="Offset for pagination"),  # 기본값 0
    limit: int = Query(10, description="Limit for pagination"),  # 기본값 10
    db: Session = Depends(utils.get_db)
):
    res = ais.get_ai_overviews(db=db, offset=offset, limit=limit)
    return res


@router.get("/id/{ai_id}", response_model=ai_schemas.AIRead)
def get_ai( ai_id: str, db: Session = Depends(utils.get_db)):
    ai_exists = ais.check_ai_exists(db, ai_id=ai_id)
    if not ai_exists:
        raise HTTPException(status_code=404, detail="AI not found")
    res = ais.get_ai_overview(db=db, ai_id=ai_id)
    return res

# @router.get("/ais/user/{user_address}", response_model=schemas.MyAIsOutList)
# def get_user_ais(user_address: str, db: Session = Depends(utils.get_db)):
#     res = ais.get_user_ais(db=db, user_address=user_address)
#     return res

# #인기있는 AI 보기
# @router.get("/ais/trend/{user_address}/{category}", response_model=schemas.AIOVerviewList)
# def get_trend_ais(
#     user_address: str,
#     category: str,
#     offset: int = Query(0, description="Offset for pagination"),  # 기본값 0
#     limit: int = Query(10, description="Limit for pagination"),  # 기본값 10
#     db: Session = Depends(utils.get_db)
# ):
#     return ais.get_category_trend_users(db=db, offset=offset, limit=limit, category=category, user_address=user_address)

# @router.get("/ais/today/{user_address}", response_model=schemas.AIOVerviewList)
# def get_today_ais(user_address : str, db: Session = Depends(utils.get_db)):
#     res = ais.get_today_ais(db=db, user_address=user_address)
#     return res

# @router.get("/ais/search/{ai_name}/{user_address}", response_model=schemas.AIOVerviewList)
# def search_ai_by_name(ai_name: str, user_address:str, db: Session = Depends(utils.get_db)):
#     res = ais.search_ai_by_name(db, name=ai_name, user_address=user_address)
#     return res


@router.post("/", response_model=base_schemas.AI)
def create_ai(ai: ai_schemas.AICreate, db: Session = Depends(utils.get_db)):
    ai_id = utils.create_ai_id(creator_address=ai.creator_address, ai_name=ai.name)

    ai_exists = ais.check_ai_exists(db=db, ai_id=ai_id)
    if ai_exists:
        raise HTTPException(status_code=400, detail="AI with this ID already exists")

    db_user = users.get_user(db, user_address=ai.creator_address)
    if not db_user:
        raise HTTPException(status_code=400, detail="You are not user")
    
    # AI 콘텐츠를 추가하는 로직
    faiss_id = ai.name + "tx" + str(random.random())
    embed = crud.add_text([ai.rag_contents], [{"source" : ai_id}], [faiss_id])
    print("embed", embed[0][0])

    # 블록체인에 ai 생성 
    # creator_address가 블록체인 address 형식이 아닐 때 HTTPExeption(status_code=400, detail="User address is not a blockchain address type")
    suiapi.add_ai(ai_id=ai_id, creator_address=ai.creator_address)

    # blob 저장
    digest = suiapi.add_blob(ai=ai, ai_id=ai_id, embed=embed)

    # RAG 테이블에 기록
    rags.create_rag(db=db, ai_id=ai_id, comments=ai.rag_comments, tx_hash=digest, faiss_id=faiss_id)
    
    return ais.create_ai(db=db, ai_id=ai_id, ai=ai)

# @router.put("/ais", response_model= schemas.AI)
# def update_ais(ai_update: schemas.AITableUserUpdateInput,db: Session = Depends(utils.get_db)):
#     db_ai = ais.get_ai(db, ai_id=ai_update.ai_id)
#     if not db_ai:
#         raise HTTPException(status_code=400, detail="AI Not found")
#     if db_ai.creator_address != ai_update.creator_address:
#         raise HTTPException(status_code=400, detail="You are not the owner of AI")

#     # AI 콘텐츠가 변경된 경우 add_text 호출
#     if ai_update.contents != "":
#         faiss_id = db_ai.ai_name + "tx" + str(random.random())
#         embed = add_text([ai_update.contents], [{"source" : ai_update.ai_id}], [faiss_id])

#         digest = suiapi.add_blob(ai=db_ai, ai_id=ai_update.ai_id, embed=embed)

#         ais.create_rag(db=db, ai_id=ai_update.ai_id, comments=ai_update.comments, digest=digest, faiss_id=faiss_id)
    
#     return ais.update_ai(db=db, ai_id=ai_update.ai_id, ai_update=ai_update)

# @router.delete("/ais", response_model=schemas.AI)
# def delete_ai(ai : schemas.AITableDelete, db: Session = Depends(utils.get_db)):

#     db_ai = ais.get_ai(db, ai_id=ai.ai_id)
#     if not db_ai:
#         raise HTTPException(status_code=404, detail="AI not found")
#     if db_ai.creator_address != ai.creator_address:
#         raise HTTPException(status_code=400, detail="You are not the owner of AI")
    
#     deleted_ai = ais.delete_ai(db=db, ai_id=ai.ai_id)

#     ai_logs = ais.get_raglogs_by_aiid(db=db, ai_id=ai.ai_id)
#     ids = [i.faiss_id for i in ai_logs]
#     delete_text(ids)

#     ais.delete_raglogs(db=db, ai_id=ai.ai_id)

#     if not deleted_ai:
#         raise HTTPException(status_code=404, detail="AI not found")
#     return deleted_ai

# # #특정 AI 로그 목록 보기
# # @router.get("/ailogs/ai/{aiid}", response_model=schemas.AILogTableListOut)
# # def read_ailog_by_aiid(aiid: str, db: Session = Depends(utils.get_db)):
# #     db_ailogs = ais.get_ailogs_by_aiid(db, aiid=aiid)
# #     if not db_ailogs:
# #         raise HTTPException(status_code=404, detail="Log not found")
# #     return schemas.AILogTableListOut(logs=db_ailogs)