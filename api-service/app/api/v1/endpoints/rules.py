from typing import Any, List

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from fastapi.encoders import jsonable_encoder

from app.api import deps
from app.core.database import get_db
from app.models.models import Rule, User
from app.schemas.schemas import RuleCreate, RuleResponse, RuleUpdate

router = APIRouter()

@router.get("/", response_model=List[RuleResponse])
def read_rules(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    active: bool = False,
    current_user: User = Depends(deps.get_current_active_user),
    factory_id: str = Depends(deps.get_factory_id)
) -> Any:
    # Factory filter mandatory
    query = db.query(Rule).filter(Rule.factory_id == factory_id)
    if active:
        query = query.filter(Rule.is_active == True)
    rules = query.offset(skip).limit(limit).all()
    return rules

@router.post("/", response_model=RuleResponse)
def create_rule(
    *,
    db: Session = Depends(get_db),
    rule_in: RuleCreate,
    current_user: User = Depends(deps.get_current_active_user),
    factory_id: str = Depends(deps.get_factory_id)
) -> Any:
    if not current_user.can_write and current_user.role != "super_admin":
        raise HTTPException(status_code=400, detail="Not enough permissions")
        
    rule = Rule(
        factory_id=factory_id,
        device_id=rule_in.device_id,
        name=rule_in.name,
        description=rule_in.description,
        conditions=[c.model_dump() for c in rule_in.conditions],
        condition_operator=rule_in.condition_operator,
        schedule_start=rule_in.schedule_start,
        schedule_end=rule_in.schedule_end,
        cooldown_seconds=rule_in.cooldown_seconds,
        auto_resolve=rule_in.auto_resolve,
        created_by=current_user.id
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule

@router.put("/{rule_id}", response_model=RuleResponse)
def update_rule(
    *,
    db: Session = Depends(get_db),
    rule_id: str,
    rule_in: RuleUpdate,
    current_user: User = Depends(deps.get_current_active_user),
    factory_id: str = Depends(deps.get_factory_id)
) -> Any:
    rule = db.query(Rule).filter(Rule.id == rule_id, Rule.factory_id == factory_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
        
    if not current_user.can_write and current_user.role != "super_admin":
         raise HTTPException(status_code=400, detail="Not enough permissions")

    rule_data = jsonable_encoder(rule)
    update_data = rule_in.model_dump(exclude_unset=True)
    for field in rule_data:
        if field in update_data:
            setattr(rule, field, update_data[field])
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule

@router.delete("/{rule_id}", response_model=RuleResponse)
def delete_rule(
    *,
    db: Session = Depends(get_db),
    rule_id: str,
    current_user: User = Depends(deps.get_current_active_user),
    factory_id: str = Depends(deps.get_factory_id)
) -> Any:
    # Soft delete: set is_active=False
    rule = db.query(Rule).filter(Rule.id == rule_id, Rule.factory_id == factory_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
        
    if not current_user.can_write and current_user.role != "super_admin":
         raise HTTPException(status_code=400, detail="Not enough permissions")

    rule.is_active = False
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule
