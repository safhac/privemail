import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from database.db import get_db, Group
from models import schemas

router = APIRouter(
    prefix="/groups",
    tags=["Groups"],
)

@router.post("/", response_model=schemas.GroupDetail)
def create_or_update_group(
    group: schemas.GroupCreate, 
    db: Session = Depends(get_db)
):
    """
    Create a new group or update an existing one based on name.
    """
    logging.info(f"Attempting to create/update group: {group.name}")
    
    db_group = db.query(Group).filter(Group.name == group.name).first()
    
    if db_group:
        # Update
        logging.info(f"Group '{group.name}' found, updating settings...")
        db_group.group_goal = group.group_goal
        db_group.group_tone = group.group_tone
        db_group.group_urgency = group.group_urgency
        db_group.color = group.color # <-- NEW
    else:
        # Create
        logging.info(f"Group '{group.name}' not found, creating new entry...")
        db_group = Group(
            name=group.name,
            group_goal=group.group_goal,
            group_tone=group.group_tone,
            group_urgency=group.group_urgency,
            color=group.color # <-- NEW
        )
        db.add(db_group)

    try:
        db.commit()
        db.refresh(db_group)
        logging.info(f"Group '{group.name}' saved successfully.")
        return db_group
    except Exception as e:
        db.rollback()
        logging.error(f"Error saving group: {e}")
        raise HTTPException(status_code=500, detail="Failed to create/update group.")

@router.get("/", response_model=List[schemas.GroupDetail])
def get_groups_list(db: Session = Depends(get_db)):
    """
    List all groups.
    """
    try:
        groups = db.query(Group).all()
        return groups
    except Exception as e:
        logging.error(f"Error fetching groups: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch groups.")

@router.delete("/{group_id}", status_code=204)
def delete_group(group_id: int, db: Session = Depends(get_db)):
    """
    Delete a group by ID.
    """
    logging.info(f"Attempting to delete group ID: {group_id}")
    db_group = db.query(Group).filter(Group.id == group_id).first()
    
    if not db_group:
        logging.warning(f"Group ID {group_id} not found for deletion.")
        raise HTTPException(status_code=404, detail="Group not found")
        
    try:
        db.delete(db_group)
        db.commit()
        logging.info(f"Group ID {group_id} deleted successfully.")
        return None
    except Exception as e:
        db.rollback()
        logging.error(f"Error deleting group: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete group.")