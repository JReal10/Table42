import os
import requests
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

class RAGSystem:
    def __init__(self, vector_store_name: str):
        """
        Initialize the RAGSystem with OpenAI client and vector store.
        """
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=self.openai_api_key)
        self.vector_store = self._initialize_vector_store(vector_store_name)

    def _initialize_vector_store(self, vector_store_name: str):
        """
        Create or retrieve an existing vector store.
        """
        existing_stores = self.client.vector_stores.list()
        for store in existing_stores.data:
            if store.name == vector_store_name:
                return store
        return self.client.vector_stores.create(name=vector_store_name)

    def get_vector_store_id(self) -> str:
        """
        Retrieve the Vector Store ID.
        """
        return self.vector_store.id

    def delete_vector_store_file(self, file_id: str):
        """
        Delete a file from the vector store using its ID.
        """
        deleted_file = self.client.vector_stores.files.delete(
            vector_store_id=self.get_vector_store_id(),
            file_id=file_id
        )
        print(deleted_file)

    def create_vector_store_file(self, document_path: str) -> str:
        """
        Upload a file and insert it into the vector store.

        Args:
            document_path (str): Path to the text file.

        Returns:
            str: The ID of the inserted vector store file.
        """
        file_response = self.client.files.create(
            file=open(document_path, "rb"),
            purpose="assistants"
        )
        file_id = file_response.id

        vector_store_file = self.client.vector_stores.files.create(
            vector_store_id=self.get_vector_store_id(),
            file_id=file_id
        )
        return vector_store_file.id

    def list_vector_store_files(self):
        """
        List all files in the vector store and print their metadata.
        """
        vector_store_files = self.client.vector_stores.files.list(
            vector_store_id=self.get_vector_store_id()
        )
        
        return (vector_store_files)

    def retrieve_vector_store_file_content(self, vector_store_id: str, file_id: str):
        """
        retrieve the content of a file stored in a vector store using OpenAI's API.

        Args:
            vector_store_id (str): The ID of the vector store.
            file_id (str): The ID of the file inside the vector store.
            save_path (str, optional): If provided, saves the file content to this path.

        Returns:
            str: The file content as a string (unless saved to disk).
        """
    
        headers = {
            "Authorization": f"Bearer {self.openai_api_key}"
        }

        url = f"https://api.openai.com/v1/vector_stores/{vector_store_id}/files/{file_id}/content"

        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.text
        else:
            return(response.status_code)
    

def main():
    rag = RAGSystem(vector_store_name="flatiron_restaurant")

    vector_store_id = rag.get_vector_store_id()
    print("VECTOR_STORE_ID:", vector_store_id)

    # Upload and insert the file into the vector store
    document_path = "flatiron_restaurant.txt"  # Make sure this file exists in the same directory
    try:
        file_id = rag.create_vector_store_file(document_path)
        print("FILE_ID:", file_id)
    except FileNotFoundError:
        print(f"❌ File '{document_path}' not found. Please check the path.")

if __name__ == "__main__":
    main()
