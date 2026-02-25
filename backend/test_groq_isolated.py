import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

load_dotenv()

class TestSchema(BaseModel):
    thinking: str = Field(description="Internal thought process")
    action: str = Field(description="The action to take")
    
def test_groq():
    key = os.getenv("GROQ_API_KEY")
    print(f"Key loaded: {'Yes' if key else 'No'}")
    try:
        llm = ChatGroq(model="llama3-70b-8192", groq_api_key=key)
        print("ChatGroq initialized.")
        structured_llm = llm.with_structured_output(TestSchema)
        print("with_structured_output succeeded.")
    except Exception as e:
        print(f"Exception caught: {e}")

if __name__ == "__main__":
    test_groq()
