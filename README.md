# Table for 2: AI-Powered Customer Service & CRM Platform for Restaurants
![image](https://github.com/user-attachments/assets/19a79f8b-ceff-41a1-ac1e-aa7a80c38e04)
Video Demo -> [Link to video demonstration](https://www.youtube.com/watch?v=tScMSV1Bi-8&ab_channel=Jamie)
## Project Overview

Table for 2 is a comprehensive AI Assistant built specifically for restaurants to bridge the gap between social media discovery and direct booking. With 58% of Gen Z diners stating they would visit more restaurants they find on social media if they could book directly, this platform solves a critical disconnect in the restaurant industry's digital customer journey.

## Features

- Customer service through a restaurant concierge chatbot
- Social media management with automated Instagram comment replies
- Direct booking capabilities from social media platforms
- Comprehensive restaurant management dashboard
- Customer data analytics and profile tracking

## Technologies Used

### Frontend (Currently Under Development)

- Next.js 15.2.3
- React 19.0.0
- TypeScript
- Tailwind CSS 4.0

The frontend is actively being developed and is not yet fully functional.

### Backend

- Python
- FastAPI
- OpenAI API (GPT-4o and GPT-4o-mini)
- Facebook/Instagram Graph API
- AipoLabs ACI for Google Calendar integration
- Vector Database for restaurant information storage

## Setup Instructions

### Prerequisites

- Python 3.8 or later
- OpenAI API key
- Facebook/Instagram Developer account
- Google Calendar API credentials (for the reservation system)

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/project-arq.git
   cd project-arq
   ```

2. **Install frontend dependencies**

   ```bash
   npm install
   ```

3. **Set up Python virtual environment**

   ```bash
   cd backend
   python -m venv ai_venv
   source ai_venv/bin/activate  # On Windows: ai_venv\Scripts\activate
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory and add the following:

   ```
   OPENAI_API_KEY=your_openai_api_key
   FACEBOOK_ACCESS_TOKEN=your_facebook_access_token
   AIPOLABS_ACI_API_KEY=your_aipolabs_api_key
   LINKED_ACCOUNT_OWNER_ID=your_google_account_id
   ```

   Create a `backend/cwdchat_config.json` file with the following structure:

   ```json
   {
     "app_id": "your_facebook_app_id",
     "app_secret": "your_facebook_app_secret",
     "redirect_uri": "your_oauth_redirect_uri"
   }
   ```

5. **Start the development server**

   Backend:

   ```bash
   cd backend
   source ai_venv/bin/activate  # On Windows: ai_venv\Scripts\activate
   python main.py
   ```

6. **Open the application**
   Visit `http://localhost:3000` in your browser

## Project Structure

```
project-arq/
├── backend/                  # Python backend
│   ├── ai_agent/            # OpenAI assistant integrations
│   ├── auth/                # Authentication for Instagram/Facebook
│   ├── helper/              # Utility functions
│   ├── tools/               # External API integrations
│   ├── vector_database/     # Restaurant information storage
│   └── main.py              # FastAPI server
├── public/                  # Static assets
├── frontend/
│   ├── app/                 # Next.js app directory
│   │   ├── conversation-history/
│   │   ├── dashboard/
│   │   ├── personalized-agent/
│   │   └── layout.tsx       # Root layout
│   └── components/          # Reusable React components
└── package.json             # Frontend dependencies
```

## Dependencies
### Backend Dependencies

- fastapi
- uvicorn
- pydantic
- python-dotenv
- openai
- openai-agents
- requests
- aipolabs

## Deployment

 **Backend Deployment**
   Depends on the hosting provider. Ensure environment variables are properly configured.

## Contributing

This project was developed by:

- **Jamie Ogundiran** - Lead Developer (https://www.linkedin.com/in/jamie-ogundiran-874aa3230/)
- **Simon Cho** - Research & Marketing (https://www.linkedin.com/in/simon-cho-a3945619a/)

## License

This project is licensed under the GNU GENERAL PUBLIC LICENSE - see the [LICENSE](LICENSE) file for details.


## Contact

For inquiries, please contact [jamieogundiran@example.com](mailto:jamieogundiran@gmail.com)
