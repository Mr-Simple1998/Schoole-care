from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Student, User, UserRole
from ..models_subject import Subject, StudentSubject
from ..security import get_current_user, get_current_principal, is_head_role, managed_campus_ids

router = APIRouter()


class SubjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=30)
    category: str = "学科"      # 学科 / 非学科
    sort: int = 0


class SubjectUpdate(BaseModel):
    name: str | None = None
    category: str | None = None
    sort: int | None = None
    is_active: bool | None = None


def _subject_out(s):
    return {
        "id": s.id, "name": s.name, "category": s.category,
        "sort": s.sort, "is_active": s.is_active,
    }


@router.get("")
def list_subjects(page: int | None = Query(default=None, ge=1), page_size: int = Query(default=10, ge=1, le=100), current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """学科列表（按分类优先、排序号排列）"""
    q = db.query(Subject).order_by(Subject.category.desc(), Subject.sort, Subject.id)
    subs = (q.offset((page - 1) * page_size).limit(page_size).all()
            if page is not None else q.all())
    return [_subject_out(s) for s in subs]


@router.get("/stats")
def subject_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """按学科/分类统计在读学生人数（用于工作台）"""
    student_q = db.query(Student).filter(Student.deleted == False)  # noqa: E712
    if current_user.role == UserRole.TEACHER:
        student_q = student_q.filter(Student.teacher_id == current_user.id)
    elif is_head_role(current_user.role):
        managed = managed_campus_ids(db, current_user) or set()
        student_q = student_q.filter(Student.campus_id.in_(managed))
    elif current_user.role == UserRole.PRINCIPAL and current_user.campus_id:
        student_q = student_q.filter(Student.campus_id == current_user.campus_id)

    # 各学科人数
    from sqlalchemy import func
    rows = (
        db.query(Subject.id, Subject.name, Subject.category, func.count(StudentSubject.student_id))
        .outerjoin(StudentSubject, StudentSubject.subject_id == Subject.id)
        .filter(Subject.is_active == True)  # noqa: E712
        .group_by(Subject.id)
        .order_by(Subject.category.desc(), Subject.sort, Subject.id)
        .all()
    )
    subject_counts = [{"id": r[0], "name": r[1], "category": r[2], "count": r[3]} for r in rows]

    # 学科类 / 非学科类 汇总（去重学生）
    active_ids = [s.id for s in student_q.all()]
    if not active_ids:
        cat_counts = {"学科": 0, "非学科": 0}
    else:
        cat_counts = {"学科": 0, "非学科": 0}
        for cat in ("学科", "非学科"):
            sub_ids = [s.id for s in db.query(Subject).filter(Subject.category == cat).all()]
            if not sub_ids:
                continue
            n = (
                db.query(Student.id)
                .join(StudentSubject, StudentSubject.student_id == Student.id)
                .filter(
                    Student.id.in_(active_ids),
                    StudentSubject.subject_id.in_(sub_ids),
                )
                .distinct()
                .count()
            )
            cat_counts[cat] = n

    return {
        "subject_counts": subject_counts,
        "category_counts": cat_counts,
        "total_students": len(active_ids),
    }


@router.post("", dependencies=[Depends(get_current_principal)])
def create_subject(data: SubjectCreate, db: Session = Depends(get_db)):
    if data.category not in ("学科", "非学科"):
        raise HTTPException(status_code=400, detail="分类只能为学科或非学科")
    if db.query(Subject).filter(Subject.name == data.name).first():
        raise HTTPException(status_code=400, detail="学科已存在")
    s = Subject(**data.model_dump())
    db.add(s)
    db.commit()
    db.refresh(s)
    return _subject_out(s)


@router.put("/{subject_id}", dependencies=[Depends(get_current_principal)])
def update_subject(subject_id: int, data: SubjectUpdate, db: Session = Depends(get_db)):
    s = db.query(Subject).filter(Subject.id == subject_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="学科不存在")
    if data.category is not None and data.category not in ("学科", "非学科"):
        raise HTTPException(status_code=400, detail="分类只能为学科或非学科")
    # 重名校验
    new_name = data.name if data.name is not None else s.name
    dup = db.query(Subject).filter(Subject.name == new_name, Subject.id != subject_id).first()
    if dup:
        raise HTTPException(status_code=400, detail="学科已存在")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(s, k, v)
    db.commit()
    db.refresh(s)
    return _subject_out(s)


@router.delete("/{subject_id}", dependencies=[Depends(get_current_principal)])
def delete_subject(subject_id: int, db: Session = Depends(get_db)):
    s = db.query(Subject).filter(Subject.id == subject_id).first()
    if not s:
        raise HTTPException(status_code=404, detail="学科不存在")
    # 解除所有学生关联
    db.query(StudentSubject).filter(StudentSubject.subject_id == subject_id).delete()
    db.delete(s)
    db.commit()
    return {"detail": "已删除"}
