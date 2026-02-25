
import json
import asyncio
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

# Mock Classes to test logic in isolation
class OrchestrationStep(BaseModel):
    thinking: str = Field(description="Internal reasoning for this step")
    action: str = Field(description="The action to take: 'DISCUSS', 'EXECUTE_SKILL', or 'COMPLETE'")
    skill_name: Optional[str] = Field(default=None, description="Name of the skill if action is 'EXECUTE_SKILL'")
    skill_input: Optional[Dict[str, Any]] = Field(default=None, description="Arguments for the skill")
    discussion_prompt: Optional[str] = Field(default=None, description="Prompt for the user if action is 'DISCUSS'")

class MockAIMessage:
    def __init__(self, content):
        self.content = content

def test_parsing_logic(step):
    print(f"Testing input type: {type(step)}")
    
    # EXACT LOGIC FROM agent.py step 1866
    if not hasattr(step, "action") or isinstance(step, (str, dict)):
        print(f"[DEBUG] Path A: Unexpected type detection triggered.")
        content = str(getattr(step, "content", step))
        print(f"[DEBUG] Raw Content Snapshot: {content[:100]}...")
        
        if "{" in content:
            try:
                start = content.find("{")
                end = content.rfind("}") + 1
                json_str = content[start:end]
                data = json.loads(json_str)
                print(f"[DEBUG] SUCCESS: Extracted JSON.")
                return OrchestrationStep(**data)
            except Exception as e:
                print(f"[DEBUG] Manual JSON parsing failed: {e}")

        if isinstance(step, dict):
            try:
                return OrchestrationStep(**step)
            except Exception as e:
                print(f"[DEBUG] Dict conversion failed: {e}")

        return f"FAILED: Unparseable {type(step)}"
    
    return "SUCCESS: Already valid model"

# Test Cases
print("--- TEST 1: RAW JSON STRING ---")
res1 = test_parsing_logic('{"thinking": "test", "action": "DISCUSS", "discussion_prompt": "hello"}')
print(f"Result 1: {res1}")

print("\n--- TEST 2: AIMessage WITH JSON ---")
msg = MockAIMessage('Here is the json: {"thinking": "reasoning", "action": "DISCUSS", "discussion_prompt": "how can I help?"} End of msg.')
res2 = test_parsing_logic(msg)
print(f"Result 2: {res2}")

print("\n--- TEST 3: DICT ---")
res3 = test_parsing_logic({"thinking": "dict test", "action": "COMPLETE"})
print(f"Result 3: {res3}")
