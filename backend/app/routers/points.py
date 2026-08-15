from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Student, User
from ..models_points import PointRecord, PointSetting, Prize, Redemption
from ..security import get_current_user

router = APIRouter()


# ---------- 积分加扣 ----------
class PointChange(BaseModel):
    student_id: int
    change: int
    reason: str | None = None
    category: str = "表现"


@router.post("/change")
def change_points(data: PointChange, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """给某学生加/扣积分"""
    student = db.query(Student).filter(Student.id == data.student_id, Student.org_id == current_user.org_id, Student.deleted == False).first()  # noqa: E712
    if not student:
        raise HTTPException(status_code=404, detail="学生不存在")
    rec = PointRecord(
        student_id=data.student_id, change=data.change, reason=data.reason,
        category=data.category, created_by=current_user.id, created_at=datetime.utcnow(),
        org_id=current_user.org_id,
    )
    student.points = (student.points or 0) + data.change
    db.add(rec)
    db.commit()
    return {"detail": "success", "student_id": student.id, "points": student.points}


@router.get("/records")
def list_point_records(student_id: int | None = None, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(PointRecord).filter(PointRecord.org_id == current_user.org_id)
    if student_id:
        q = q.filter(PointRecord.student_id == student_id)
    recs = q.order_by(PointRecord.created_at.desc()).all()
    result = []
    for r in recs:
        st = db.query(Student).filter(Student.id == r.student_id, Student.org_id == current_user.org_id).first()
        result.append({
            "id": r.id, "student_id": r.student_id, "student_name": st.name if st else "",
            "change": r.change, "reason": r.reason, "category": r.category,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    return result


# ---------- 积分规则 ----------
class SettingCreate(BaseModel):
    name: str
    category: str = "表现"
    change: int
    description: str | None = None


@router.get("/settings")
def list_settings(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(PointSetting).filter(PointSetting.org_id == current_user.org_id).all()


@router.post("/settings")
def create_setting(data: SettingCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    s = PointSetting(**data.model_dump(), org_id=current_user.org_id)
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


# ---------- 奖品 ----------
class PrizeCreate(BaseModel):
    name: str
    description: str | None = None
    cost_points: int
    stock: int = 0
    image: str | None = None


@router.get("/prizes")
def list_prizes(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Prize).filter(Prize.is_active == True, Prize.org_id == current_user.org_id).all()  # noqa: E712


@router.post("/prizes")
def create_prize(data: PrizeCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    p = Prize(**data.model_dump(), created_at=datetime.utcnow(), org_id=current_user.org_id)
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


# ---------- 兑换 ----------
class RedeemCreate(BaseModel):
    student_id: int
    prize_id: int


@router.post("/redeem")
def redeem(data: RedeemCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    student = db.query(Student).filter(Student.id == data.student_id, Student.org_id == current_user.org_id, Student.deleted == False).first()  # noqa: E712
    prize = db.query(Prize).filter(Prize.id == data.prize_id, Prize.is_active == True, Prize.org_id == current_user.org_id).first()  # noqa: E712
    if not student or not prize:
        raise HTTPException(status_code=404, detail="学生或奖品不存在")
    if (student.points or 0) < prize.cost_points:
        raise HTTPException(status_code=400, detail="积分不足")
    if prize.stock == 0:
        raise HTTPException(status_code=400, detail="奖品已兑换完")
    if prize.stock > 0:
        prize.stock -= 1
    student.points -= prize.cost_points
    r = Redemption(
        student_id=data.student_id, prize_id=data.prize_id, cost_points=prize.cost_points,
        created_by=current_user.id, created_at=datetime.utcnow(), org_id=current_user.org_id,
    )
    db.add(r)
    db.commit()
    return {"detail": "兑换成功", "points": student.points}


@router.get("/redemptions")
def list_redemptions(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    recs = db.query(Redemption).filter(Redemption.org_id == current_user.org_id).order_by(Redemption.created_at.desc()).all()
    result = []
    for r in recs:
        st = db.query(Student).filter(Student.id == r.student_id, Student.org_id == current_user.org_id).first()
        pz = db.query(Prize).filter(Prize.id == r.prize_id, Prize.org_id == current_user.org_id).first()
        result.append({
            "id": r.id, "student_id": r.student_id, "student_name": st.name if st else "",
            "prize_id": r.prize_id, "prize_name": pz.name if pz else "",
            "cost_points": r.cost_points, "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    return result


# ---------- 排行榜 ----------
@router.get("/leaderboard")
def leaderboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(Student).order_by(Student.points.desc())
    q = q.filter(Student.org_id == current_user.org_id, Student.deleted == False)  # noqa: E712
    if current_user.role == "teacher":
        q = q.filter(Student.teacher_id == current_user.id)
    students = q.limit(50).all()
    return [{"id": s.id, "name": s.name, "points": s.points or 0, "rank": i + 1} for i, s in enumerate(students)]