import anthropic
from typing import Optional
from datetime import datetime

class ClaudeAIService:
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20240620"):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
        # Fallback models to try if the primary fails
        self.fallback_models = [
            "claude-3-5-sonnet-20240620",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307"
        ]
    
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
4. Use all the attendee names mentioned in the transcript
5. Keep the content concise but comprehensive
6. Use bullet points and numbered lists for clarity
7. Replace {{project_name}} with the actual project name: {project_name or "Meeting Project"}
8. Replace {{meeting_date}} with today's date: {datetime.now().strftime('%Y-%m-%d')}
9. For "Prepared by", try to identify who might be the meeting organizer/facilitator from the transcript, or use "MoM Agent" if unclear

{f"Previous meeting context for this project: {project_context}" if project_context else ""}

IMPORTANT:
- Start your response directly with "**Minutes of Meeting**"
- Do NOT include any introductory text like "Here are the Minutes..." or "Based on the transcript..."
- Generate the MoM in markdown format following the template structure exactly
- Extract real content from the transcript, not placeholder text"""
        
        user_prompt = f"Please analyze this meeting transcript and generate a structured Minutes of Meeting:\n\n{transcript}"
        
        # Try primary model first, then fallbacks
        models_to_try = [self.model] + self.fallback_models

        for model in models_to_try:
            try:
                response = self.client.messages.create(
                    model=model,
                    max_tokens=2000,
                    temperature=0.3,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": user_prompt}
                    ]
                )

                if response.content and len(response.content) > 0:
                    content = response.content[0].text

                    # Clean up any unwanted prefixes
                    unwanted_prefixes = [
                        "Here are the Minutes of Meeting based on the provided transcript:",
                        "Based on the provided transcript, here are the Minutes of Meeting:",
                        "Here is the structured Minutes of Meeting:",
                        "Based on the transcript:",
                        "Here are the minutes:"
                    ]

                    for prefix in unwanted_prefixes:
                        if content.strip().startswith(prefix):
                            content = content.strip()[len(prefix):].strip()

                    # Replace template placeholders
                    content = content.replace("{project_name}", project_name or "Meeting Project")
                    content = content.replace("{meeting_date}", datetime.now().strftime('%Y-%m-%d'))
                    content = content.replace("[Name]", "MoM Agent")

                    return content

            except anthropic.APIError as e:
                print(f"Model {model} failed: {e}")
                if model == models_to_try[-1]:  # Last model in list
                    return f"""**Minutes of Meeting**

**Project Name:** {project_name or "Meeting Project"}
**Meeting Date:** {datetime.now().strftime('%Y-%m-%d')}

**Error:** All Claude models failed
**Last Error:** {str(e)}

**Tried Models:** {', '.join(models_to_try)}

Please check your API key or try again later."""
                continue  # Try next model
            except Exception as e:
                print(f"Unexpected error with model {model}: {e}")
                continue

        # If we get here, all models failed
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