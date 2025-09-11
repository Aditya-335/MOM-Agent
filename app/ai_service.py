import anthropic
from typing import Optional
from datetime import datetime

class ClaudeAIService:
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
    
    def generate_mom(self, transcript: str, project_context: str = "", project_name: str = "") -> Optional[str]:
        """Generate Minutes of Meeting from transcript using Claude"""
        
        # MoM template
        mom_template = """
**Minutes of Meeting**

**Project Name:** {project_name}
**Meeting Date:** {meeting_date}
**Meeting Attendees:** 
- 

**Discussion Points:**
1. 

**Decisions Made:**
1. 

**Action Items:**

**Client Team:**
- [ ] 

**Spikra Team:**
- [ ] 

**Prepared by:** [Name]
        """.strip()
        
        system_prompt = f"""You are an AI assistant specialized in generating structured Minutes of Meeting (MoM) from meeting transcripts.

Your task is to analyze the provided meeting transcript and generate a well-structured MoM using the following template:

{mom_template}

Guidelines:
1. Extract key discussion points from the transcript
2. Identify clear decisions that were made during the meeting
3. Separate action items between Client Team and Spikra Team based on context
4. Use the attendee names mentioned in the transcript
5. Keep the content concise but comprehensive
6. Use bullet points and numbered lists for clarity
7. Replace {{project_name}} with the actual project name: {project_name or "Meeting Project"}
8. Replace {{meeting_date}} with today's date: {datetime.now().strftime('%Y-%m-%d')}

{f"Previous meeting context for this project: {project_context}" if project_context else ""}

Generate the MoM in markdown format following the template structure exactly. Make sure to extract real content from the transcript, not placeholder text."""
        
        user_prompt = f"Please analyze this meeting transcript and generate a structured Minutes of Meeting:\n\n{transcript}"
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0.3,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            if response.content and len(response.content) > 0:
                content = response.content[0].text
                # Replace template placeholders
                content = content.replace("{project_name}", project_name or "Meeting Project")
                content = content.replace("{meeting_date}", datetime.now().strftime('%Y-%m-%d'))
                return content
            else:
                return None
                
        except anthropic.APIError as e:
            print(f"Anthropic API Error: {e}")
            return f"""**Minutes of Meeting**

**Project Name:** {project_name or "Meeting Project"}
**Meeting Date:** {datetime.now().strftime('%Y-%m-%d')}

**Error:** API request failed
**Details:** {str(e)}

Please check your API key and try again."""
        except Exception as e:
            print(f"Unexpected error: {e}")
            return None
    
    def test_connection(self) -> bool:
        """Test if the API connection is working"""
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=10,
                messages=[
                    {"role": "user", "content": "Hello, please respond with 'OK'"}
                ]
            )
            return response.content and len(response.content) > 0
        except:
            return False