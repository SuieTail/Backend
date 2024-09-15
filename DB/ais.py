from sqlalchemy.orm import Session
from . import models, schemas
from datetime import datetime

################### AITable CRUD functions ###################

def get_ais(db: Session, offset: int, limit: int):
    return db.query(models.AITable).offset(offset).limit(limit-offset).all()

def get_ai(db: Session, ai_id: str):
    return db.query(models.AITable).filter(models.AITable.ai_id == ai_id).first()

def get_user_ais(db: Session, user_address : str):
    return db.query(models.AITable).filter(models.AITable.creator_address == user_address).all()

def get_rags(db: Session, ai_id: str):
    return db.query(models.RAGTable).filter(models.AITable.ai_id == ai_id).all()

def get_ai_detail(db: Session, ai_id: str) -> schemas.AIDetail:
    # AITable과 RAGTable을 ai_id로 조인
    result = (
        db.query(models.AITable, models.RAGTable)
        .join(models.RAGTable, models.AITable.ai_id == models.RAGTable.ai_id)
        .filter(models.AITable.ai_id == ai_id)
        .all()
    )
    
    if not result:
        return None  # 해당 ai_id에 대한 데이터가 없는 경우 처리
    
    # AITable 정보는 첫 번째 레코드에서 가져옵니다
    ai, _ = result[0]

    # RAGTable 데이터는 모든 레코드에서 logs로 변환합니다
    logs = [schemas.RAGTableBase.model_validate(rag) for _, rag in result]

    # AIDetail 스키마로 반환
    ai_detail = schemas.AIDetail(
        ai_id=ai.ai_id,
        creator_address=ai.creator_address,
        created_at=ai.created_at,
        name=ai.name,
        image_url=ai.image_url,
        category=ai.category,
        introductions=ai.introductions,
        chat_counts=ai.chat_counts,
        prompt_tokens=ai.prompt_tokens,
        completion_tokens=ai.completion_tokens,
        weekly_users=ai.weekly_users,
        logs=logs  # logs는 RAGTableBase 리스트로 설정
    )
    
    return ai_detail


def get_ais_by_weekly_users(db: Session, offset: int, limit : int):
    return db.query(models.AITable).order_by(models.AITable.weekly_users.desc()).offset(offset).limit(limit - offset).all()

def get_today_ais(db: Session):
    # Join the tables and fetch the data
    results = db.query(models.AITable, models.UserTable)\
        .join(models.UserTable, models.AITable.creator_address == models.UserTable.user_address)\
        .order_by(models.AITable.created_at.desc())\
        .limit(4).all()

    ais = []
    # Manually map each result to the AITableOut schema
    for ait, user in results:
        ai_out = schemas.AITableOut(
            ai_id=ait.ai_id,
            creator_address=ait.creator_address,
            created_at=ait.created_at,
            name=ait.name,
            image_url=ait.image_url,
            category=ait.category,
            introductions=ait.introductions,
            chat_counts=ait.chat_counts,
            prompt_tokens=ait.prompt_tokens,
            completion_tokens=ait.completion_tokens,
            weekly_users=ait.weekly_users,
            creator=user.nickname  # Mapping the nickname to the `creator` field
        )
        ais.append(ai_out)
    
    return ais

def get_category_ais_by_weekly_users(db: Session, offset: int, limit : int, category:str):
    return db.query(models.AITable).filter(models.AITable.category == category).order_by(models.AITable.weekly_users.desc()).offset(offset).limit(limit - offset).all()

def search_ai(db: Session, name: str):
    return db.query(models.AITable).filter(models.AITable.name.like(f"%{name}%")).all()

# # AITable CRUD functions
# def get_top_10_ai_by_usage(db: Session):
#     return db.query(models.AITable).order_by(models.AITable.usage.desc()).limit(10).all()

def create_ai(db: Session,ai_id:str, ai: schemas.AITableCreate):
    aiDB = schemas.AITableBase(
        ai_id = ai_id,
        creator_address =  ai.creator_address,
        created_at = datetime.now(),
        name = ai.name,
        image_url = ai.image_url,
        category = ai.category,
        introductions = ai.introductions,
        chat_counts=0,
        prompt_tokens=0,
        completion_tokens=0,
        weekly_users = 0
    )

    db_ai = models.AITable(**aiDB.model_dump())
    db.add(db_ai)
    db.commit()
    db.refresh(db_ai)
    return db_ai

def update_ai(db: Session, ai_id: str, ai_update: schemas.AITableUserUpdateInput):
    aiUpdateDB = schemas.AITableUpdate(
        name = ai_update.name,
        image_url = ai_update.image_url,
        category= ai_update.category,  # 카테고리 필드, None이 기본값
        introductions=ai_update.introductions  # 소개 필드, None이 기본값
    )
    
    db_ai = get_ai(db, ai_id)
    if db_ai:
        for key, value in aiUpdateDB.model_dump(exclude_unset=True).items():
            setattr(db_ai, key, value)
        db.commit()
        db.refresh(db_ai)
    return db_ai

def update_usage_ai(db: Session, ai_id: str, ai_update: schemas.AITableUsageUpdate):
    db_ai = get_ai(db, ai_id)
    if db_ai:
        for key, value in ai_update.model_dump(exclude_unset=True).items():
            setattr(db_ai, key, value)
        db.commit()
        db.refresh(db_ai)
    return db_ai

# def update_collect_ai(db: Session, aiid: str, ai_update: schemas.AITableCollectUpdate):
#     db_ai = get_ai(db, aiid)
#     if db_ai:
#         for key, value in ai_update.model_dump(exclude_unset=True).items():
#             setattr(db_ai, key, value)
#         db.commit()
#         db.refresh(db_ai)
#     return db_ai

def delete_ai(db: Session, ai_id: str):
    db_ai = get_ai(db, ai_id)
    if db_ai:
        db.delete(db_ai)
        db.commit()
    return db_ai

# # AILogTable CRUD functions
# def get_ailog(db: Session, log_id: str):
#     return db.query(models.AILogTable).filter(models.AILogTable.id == log_id).first()

# # RAGTable CRUD functions
def get_raglogs_by_aiid(db: Session, ai_id: str):
    return db.query(models.RAGTable).filter(models.RAGTable.ai_id == ai_id).all()

# def create_rag(db: Session, ai_update: schemas.AITableUserUpdateInput, digest: str, faiss_id: str):
def create_rag(db: Session, ai_id: str, comments: str, digest: str, faiss_id: str):
    rag = schemas.RAGTableCreate(
        ai_id = ai_id,
        created_at = datetime.now(),
        comments = comments,
        tx_url= digest,
        faissid = faiss_id
    )
    db_rag = models.RAGTable(**rag.model_dump())
    db.add(db_rag)
    db.commit()
    db.refresh(db_rag)
    return db_rag

# def update_ailog(db: Session, log_id: str, ailog_update: schemas.AILogTableCreate):
#     db_ailog = get_ailog(db, log_id)
#     if db_ailog:
#         for key, value in ailog_update.model_dump(exclude_unset=True).items():
#             setattr(db_ailog, key, value)
#         db.commit()
#         db.refresh(db_ailog)
#     return db_ailog

# def delete_ailog(db: Session, log_id: str):
#     db_ailog = get_ailog(db, log_id)
#     if db_ailog:
#         db.delete(db_ailog)
#         db.commit()
#     return db_ailog

def delete_raglogs(db: Session, ai_id: str):
    # AI ID와 관련된 모든 로그를 가져옴
    ailogs = get_raglogs_by_aiid(db, ai_id)

    if not ailogs:
        return None  # 로그가 없으면 None 반환

    # 각 로그를 순회하며 삭제
    for log in ailogs:
        db.delete(log)

    # 모든 로그를 삭제한 후 commit
    db.commit()

    return ailogs  # 삭제된 로그 목록 반환