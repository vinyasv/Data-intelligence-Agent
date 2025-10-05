#!/usr/bin/env python3
"""
Simple FastAPI server for Data Intelligence Agent
Serves static HTML and provides API endpoint for chat
"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import asyncio
from typing import Optional

# Import agent
from agent_main import AgentScraper

app = FastAPI(title="Data Intelligence Agent")

# Initialize agent
agent: Optional[AgentScraper] = None

@app.on_event("startup")
async def startup_event():
    """Initialize agent on startup"""
    global agent
    try:
        agent = AgentScraper()
        print("✅ Agent initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Chat endpoint"""
    if not agent:
        raise HTTPException(status_code=500, detail="Agent not initialized")
    
    try:
        # Get agent response
        response_parts = []
        async for chunk in agent.chat(request.message):
            response_parts.append(chunk)
        
        full_response = "".join(response_parts)
        return ChatResponse(response=full_response)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Serve static files
app.mount("/", StaticFiles(directory="static", html=True), name="static")


if __name__ == "__main__":
    import uvicorn
    import os
    
    port = int(os.getenv("PORT", 8000))
    
    print("\n" + "="*70)
    print("🚀 Data Intelligence Agent Server")
    print("="*70)
    print(f"\n📍 Running on port {port}\n")
    
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
