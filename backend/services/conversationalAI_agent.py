import sys
import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

class ReactAgent:
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # Initialize memory, model, and tools
        self.memory = MemorySaver()
        self.model = init_chat_model("gpt-4o-mini", model_provider="openai", api_key=self.openai_api_key)
        self.tools = []
        
        # Create the agent executor using the react agent
        self.agent_executor = create_react_agent(self.model, self.tools, checkpointer=self.memory)

    @staticmethod
    def termination_tool(query: str) -> str:
        """
        Checks if the query contains any ending phrases.
        If an ending phrase is detected, the process is terminated.
        """
        ending_phrases = ["goodbye", "bye", "exit", "quit"]
        if any(phrase in query.lower() for phrase in ending_phrases):
            sys.exit("Ending phrase detected. Terminating agent.")
        return "No termination phrase detected."

    @staticmethod
    def pinecone_rag_lookup(query: str) -> str:
        """
        Placeholder function for accessing the RAG vector storage from Pinecone.
        You can later integrate your Pinecone retrieval logic here.
        """
        return "Pinecone RAG lookup not implemented yet."

    def run_interactive(self):
        """
        Runs an interactive loop, asking for user input and processing it through the agent.
        The loop continues until a termination phrase is entered or the agent invokes the termination tool.
        """
        print("Interactive Agent Started. Type your message or 'quit' to exit.")
        config = {"configurable": {"thread_id": "abc123"}}
        
        while True:
            # Ask for user input
            user_input = input(">> ")
            
            # Check for termination phrases in the user input
            self.termination_tool(user_input)
            
            # Build the message payload for the agent
            messages = [HumanMessage(content=user_input)]
            
            # Process the input through the agent and stream the response
            for step in self.agent_executor.stream(
                {"messages": messages},
                config,
                stream_mode="values",
            ):
                # Print the agent's response
                step["messages"][-1].pretty_print()


if __name__ == "__main__":
    agent = ReactAgent()
    agent.run_interactive()
