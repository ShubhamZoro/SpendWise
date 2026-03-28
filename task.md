# Smart Family Expense Tracker & AI Recommendation App

## 1. Setup & Environments
- [ ] Initialize React Native (Expo) project (`npx create-expo-app`)
- [ ] Install App Dependencies (React Navigation, Zustand, React Native Paper, victory-native, supabase-js, axios)
- [ ] Initialize Python FastAPI backend
- [ ] Install FastAPI Dependencies (fastapi, uvicorn, pandas, scikit-learn, supabase, openai)

## 2. Supabase Configuration (Database & Auth)
- [ ] Create Database Tables (`users`, `groups`, `group_members`, `expenses`)
- [ ] Set up Row Level Security (RLS) policies
- [ ] Implement Supabase Auth helpers (Signup/Login/Session persistence)
- [ ] Setup Supabase real-time subscriptions for `expenses`

## 3. Python FastAPI (AI/ML Service)
- [ ] Setup API Endpoints (`/recommendations`, `/analytics`)
- [ ] Build ML Pipeline (KMeans clustering for categorization/patterns)
- [ ] Build Anomaly Detection (Isolation Forest for overspending/spikes)
- [ ] Setup OpenAI integration for OCR (receipt parsing) endpoint (`/ocr`)
- [ ] Format AI outputs into user-friendly insights

## 4. Mobile Frontend - Core App
- [ ] Setup Navigation (Bottom Tabs, Auth Stack)
- [ ] Screen: Login / Signup (Email/Password)
- [ ] Screen: Profile & Group Management (Create/Join via Code)
- [ ] Screen: Dashboard (victory-native Charts, Category Breakdown, Monthly Trends)

## 5. Mobile Frontend - Expense Features
- [ ] Screen: Add Expense (Form with OpenAI OCR Image Upload)
- [ ] Screen: Expense History (Filtering by date and category)
- [ ] Screen: Insights (Display AI recommendations and anomaly alerts)
- [ ] Hook up state management (Zustand) with API & Supabase Client

## 6. Polish & Bonus
- [ ] Push Notifications for Overspending alerts (optional/bonus)
- [ ] UI Polish with React Native Paper
