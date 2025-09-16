import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

@dataclass
class Meeting:
    id: str
    title: str
    date: str
    transcript: str = ""
    draft_mom: str = ""
    final_mom: str = ""
    attendees: List[str] = None
    
    def __post_init__(self):
        if self.attendees is None:
            self.attendees = []

@dataclass
class Project:
    name: str
    created_date: str
    meetings: List[Meeting] = None
    
    def __post_init__(self):
        if self.meetings is None:
            self.meetings = []

class DataManager:
    def __init__(self, base_dir: str = "data"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
    
    def get_projects(self) -> List[str]:
        """Get list of all project names"""
        if not self.base_dir.exists():
            return []
        return [p.name for p in self.base_dir.iterdir() if p.is_dir()]
    
    def create_project(self, project_name: str) -> bool:
        """Create a new project directory"""
        project_dir = self.base_dir / project_name
        if project_dir.exists():
            return False
        
        project_dir.mkdir(exist_ok=True)
        project = Project(
            name=project_name,
            created_date=datetime.now().isoformat()
        )
        self._save_project_metadata(project_name, project)
        return True
    
    def get_project_meetings(self, project_name: str) -> List[Dict]:
        """Get all meetings for a project"""
        project_dir = self.base_dir / project_name
        if not project_dir.exists():
            return []
        
        meetings = []
        for meeting_file in project_dir.glob("meeting_*.json"):
            try:
                with open(meeting_file, 'r', encoding='utf-8') as f:
                    meeting_data = json.load(f)
                    meetings.append(meeting_data)
            except Exception:
                continue
        
        # Sort by date
        meetings.sort(key=lambda x: x.get('date', ''), reverse=True)
        return meetings
    
    def create_meeting(self, project_name: str, meeting_title: str) -> str:
        """Create a new meeting and return its ID"""
        project_dir = self.base_dir / project_name
        if not project_dir.exists():
            raise ValueError(f"Project {project_name} does not exist")
        
        meeting_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        meeting = Meeting(
            id=meeting_id,
            title=meeting_title,
            date=datetime.now().strftime('%Y-%m-%d %H:%M')
        )
        
        meeting_file = project_dir / f"meeting_{meeting_id}.json"
        with open(meeting_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(meeting), f, indent=2, ensure_ascii=False)
        
        return meeting_id
    
    def get_meeting(self, project_name: str, meeting_id: str) -> Optional[Dict]:
        """Get a specific meeting by ID"""
        meeting_file = self.base_dir / project_name / f"meeting_{meeting_id}.json"
        if not meeting_file.exists():
            return None
        
        try:
            with open(meeting_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
    
    def save_meeting(self, project_name: str, meeting_data: Dict) -> bool:
        """Save meeting data"""
        meeting_file = self.base_dir / project_name / f"meeting_{meeting_data['id']}.json"
        try:
            with open(meeting_file, 'w', encoding='utf-8') as f:
                json.dump(meeting_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False
    
    def get_project_context(self, project_name: str) -> str:
        """Get context from previous meetings in the project"""
        meetings = self.get_project_meetings(project_name)
        if not meetings:
            return ""
        
        context_parts = []
        for meeting in meetings[-5:]:  # Last 5 meetings for context
            if meeting.get('final_mom') or meeting.get('draft_mom'):
                mom_content = meeting.get('final_mom') or meeting.get('draft_mom')
                context_parts.append(f"Previous meeting ({meeting.get('date', '')}):\n{mom_content}\n")
        
        return "\n".join(context_parts)
    
    def delete_meeting(self, project_name: str, meeting_id: str) -> bool:
        """Delete a specific meeting"""
        meeting_file = self.base_dir / project_name / f"meeting_{meeting_id}.json"
        try:
            if meeting_file.exists():
                meeting_file.unlink()
                return True
            return False
        except Exception:
            return False

    def delete_project(self, project_name: str) -> bool:
        """Delete entire project and all its meetings"""
        import shutil
        project_dir = self.base_dir / project_name
        try:
            if project_dir.exists():
                shutil.rmtree(project_dir)
                return True
            return False
        except Exception:
            return False

    def _save_project_metadata(self, project_name: str, project: Project):
        """Save project metadata"""
        project_file = self.base_dir / project_name / "project.json"
        with open(project_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(project), f, indent=2, ensure_ascii=False)