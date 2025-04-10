# Project ARQ: Flatiron Restaurant Dashboard

## Project Overview

Project ARQ is a comprehensive AI Assistant built for Restaurants. Features include:

- Customer service through a restaurant concierge chatbot
- Social media management with automated Instagram comment replies

The application utilizes advanced AI technologies to enhance customer interactions and streamline restaurant operations. The dashboard provides an intuitive interface for staff to monitor and manage all digital customer touchpoints from a single platform.

## Features

- **Instagram Integration**: Automated comment replies and direct message handling
- **OpenAI Integration**: Leverages GPT models for natural language understanding and generation
- **Vector Database**: Stores restaurant information for accurate responses to customer queries

## Technologies Used

### Frontend

- Next.js 15.2.3
- React 19.0.0
- TypeScript
- Tailwind CSS 4.0

### Backend

- Python
- FastAPI
- OpenAI API (GPT-4o and GPT-4o-mini)
- Twilio for voice call handling
- Facebook/Instagram Graph API
- AipoLabs ACI for Google Calendar integration
- Vector Database for restaurant information storage

## Setup Instructions

### Prerequisites

- Node.js 18.x or later
- Python 3.8 or later
- OpenAI API key
- Facebook/Instagram Developer account
- Twilio account (for voice features)
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
   TWILIO_ACCOUNT_SID=your_twilio_sid
   TWILIO_AUTH_TOKEN=your_twilio_auth_token
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

   Frontend:

   ```bash
   # In the root directory
   npm run dev
   ```

   Backend:

   ```bash
   # In another terminal window
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
├── src/
│   ├── app/                 # Next.js app directory
│   │   ├── conversation-history/
│   │   ├── dashboard/
│   │   ├── personalized-agent/
│   │   └── layout.tsx       # Root layout
│   └── components/          # Reusable React components
└── package.json             # Frontend dependencies
```

## Dependencies

### Frontend Dependencies

- react: ^19.0.0
- react-dom: ^19.0.0
- next: 15.2.3

### Backend Dependencies

- fastapi
- uvicorn
- pydantic
- python-dotenv
- openai
- openai-agents
- requests
- aipolabs
- langgraph
- twilio
- websockets

## Deployment

The application can be deployed to Vercel for the frontend and a suitable Python hosting service for the backend (such as Heroku, AWS, or GCP).

1. **Frontend Deployment (Vercel)**

   ```bash
   npm run build
   # Then deploy using Vercel CLI or GitHub integration
   ```

2. **Backend Deployment**
   Depends on the hosting provider. Ensure environment variables are properly configured.

## Contributing

This project was developed by:

- **Jamie Ogundiran** - Lead Developer (Code Implementation)
- **Simon Cho** - Research & Marketing

## License

This project is proprietary and intended for exclusive use by Flatiron Restaurant.

## Contact

For inquiries, please contact [jamieogundiran@example.com](mailto:jamieogundiran@gmail.com)
