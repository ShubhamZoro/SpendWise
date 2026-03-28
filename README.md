# Family Expense Tracker

A React Native mobile app for tracking family expenses with a Python FastAPI backend.

[**Read the Onboarding & Architecture Guide 📖**](./ONBOARDING.md)

## Tech Stack

- **Frontend:** React Native with Expo
- **Backend:** Python FastAPI
- **Database:** Supabase
- **State Management:** Zustand

## Prerequisites

- Node.js (v18+)
- Python (v3.9+)
- npm or yarn
- Supabase account

## Setup

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your Supabase credentials

# Run the backend server
python main.py
```

The backend will run at `http://localhost:8000`

### 2. Frontend Setup

```bash
cd FamilyExpenseTracker

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env with your Supabase URL and API key

# Start the Expo development server
npm start
```

## Running the App

### Option 1: Expo (Recommended)
```bash
npm start
```
Then press:
- `a` for Android emulator
- `i` for iOS simulator
- `w` for web

### Option 2: Direct
```bash
npm run android
npm run ios
```

## Project Structure

```
Family Assignment/
├── FamilyExpenseTracker/    # React Native frontend
│   ├── screens/             # App screens
│   ├── services/            # API clients
│   ├── store/               # State management
│   └── constants/           # Theme and constants
├── backend/                 # Python FastAPI backend
│   ├── main.py              # API endpoints
│   ├── ocr_service.py       # Receipt OCR
│   └── ml_pipeline.py       # ML predictions
└── Schema.sql               # Database schema
```
