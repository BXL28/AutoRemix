import os
from typing import TypedDict, List
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from langgraph.graph import StateGraph, END

# Load env variables (GOOGLE_API_KEY)
load_dotenv()

class AgentState(TypedDict):
    base_track_title: str
    base_track_artist: str
    base_track_genre: str
    recommendations: List[dict] # {title, artist, reason, genre, bpm}
    error: str

# Initialize Gemini Flash Model
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.7,
)

def analyze_and_recommend(state: AgentState) -> AgentState:
    """Uses LLM to recommend 3 tracks that would remix well with the base track."""
    
    sys_prompt = """You are an expert DJ and music producer. 
Your goal is to recommend 3 songs that would make an incredible mashup or remix when combined with the user's selected base track.
Rely on your internal knowledge to estimate the BPM, Key, and Genre of the base track, and suggest 3 tracks that are harmonically compatible (similar key) or rhythmically compatible (similar or half/double BPM).

Output EXACTLY in this JSON format (no markdown blocks, no other text):
[
  {"title": "Song Title", "artist": "Artist Name", "genre": "Genre", "bpm": "120", "reason": "Why this works well (e.g. matching keys and complementary basslines)"},
  ...
]
"""
    
    user_prompt = f"Base Track: '{state['base_track_title']}' by {state['base_track_artist']}. Genre info: {state.get('base_track_genre', 'Unknown')}.\nProvide 3 remix recommendations."
    
    try:
        messages = [
            SystemMessage(content=sys_prompt),
            HumanMessage(content=user_prompt)
        ]
        
        response = llm.invoke(messages)
        content = response.content.strip()
        
        # Clean up potential markdown formatting from the model
        if content.startswith("```json"):
            content = content[7:]
        if content.endswith("```"):
            content = content[:-3]
            
        print("--- RAW CONTENT ---")
        print(content.strip())
        print("-------------------")
        
        import json
        recommendations = json.loads(content.strip())
        state['recommendations'] = recommendations
        
    except Exception as e:
        state['error'] = f"Failed to generate recommendations: {str(e)}"
        
    return state

# Build the Graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("recommend", analyze_and_recommend)

# Define edges
workflow.set_entry_point("recommend")
workflow.add_edge("recommend", END)

# Compile
remix_agent = workflow.compile()

if __name__ == "__main__":
    print("Testing LangGraph Agent...")
    initial_state = {
        "base_track_title": "Blinding Lights",
        "base_track_artist": "The Weeknd",
        "base_track_genre": "Synthwave",
        "recommendations": [],
        "error": ""
    }
    
    result = remix_agent.invoke(initial_state)
    if result.get("error"):
        print(f"Error: {result['error']}")
    else:
        for i, rec in enumerate(result['recommendations']):
            print(f"{i+1}. {rec['title']} by {rec['artist']} ({rec['bpm']} BPM)")
            print(f"   Reason: {rec['reason']}\n")
