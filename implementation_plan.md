# Goal Description
Build a "Smart Family Expense Tracker & AI Recommendation App" using React Native (Expo) for the frontend, Supabase for authentication and PostgreSQL database, and Python FastAPI for an AI recommendation service. The app allows users to manage expenses within groups and utilizes machine learning pipelines (pandas, scikit-learn) and OpenAI for smart insights, anomaly detection, and receipt OCR.

## User Review Required
> [!IMPORTANT]
> - Should we use an existing Supabase project, or do you want the raw SQL schema to deploy on a fresh Supabase project yourself?
> - For OCR (OpenAI Vision API), do you have an OpenAI API key ready to use, or should we mock this data for now? 
> - By default, we will implement this as a standard Expo project (Managed Workflow) so it's easy for you to run and test on your own device using Expo Go. Is this acceptable?

## Proposed Changes

### Supabase Database
#### [NEW] `schema.sql`
- **Users**: Extended user fields if necessary (integrated with Supabase Auth schema).
- **Groups**: `id`, `name`, `created_by`.
- **Group Members**: Junction table `id`, `user_id`, `group_id`.
- **Expenses**: `id`, `user_id`, `group_id`, `amount`, `category`, `date`, `notes`.
- Includes RLS (Row Level Security) policies so users can only access data belonging to groups they are part of.

### Mobile Frontend (Expo + React Native)
#### [NEW] `package.json`
- React Native Paper for UI components, Zustand for state management, React Navigation for routing, `victory-native` for data visualization.
#### [NEW] `services/supabaseClient.js`
- Connects to Supabase using `supabase-js`, handling Auth flow (email/password login) and token refresh, using `AsyncStorage`.
#### [NEW] `store/index.js` (Zustand)
- Store session, active group info, and general UI state.
#### [NEW] `screens/AuthScreen.js`
- Email/password authentication flow.
#### [NEW] `screens/GroupScreen.js`
- Create a group or join via an invite code.
#### [NEW] `screens/AddExpenseScreen.js`
- Input form. Includes an OCR feature where users can upload receipt images sent to FastAPI, which processes them using OpenAI.
#### [NEW] `screens/DashboardScreen.js`
- Shows charts (category-wise spending, monthly trends) using `victory-native`.
#### [NEW] `screens/ExpenseHistoryScreen.js`
- List and filter functionalities via Supabase queries.
#### [NEW] `screens/InsightsScreen.js`
- Renders human-readable tips generated from the FastAPI service.

### Backend AI/ML (FastAPI)
#### [NEW] `main.py`
- Exposes REST built on FastAPI (`/recommendations`, `/analytics`, `/ocr`).
#### [NEW] `ml_pipeline.py`
- Uses `pandas` and `scikit-learn` to apply KMeans clustering (to detect distinct spending patterns or repetitive expenses) and Isolation Forest (to identify overspending anomalies or unusual spikes in specific categories).
- Prepares insights in a structured JSON payload for the Mobile app to consume.
#### [NEW] `ocr_service.py`
- Wrapper for OpenAI's Vision model to extract `amount`, `date`, `category`, and `notes` from an image base64. 

## Verification Plan

### Automated Tests
- Test FastAPI routes with Pytest to guarantee valid AI insight structures and OCR parsing correctness.

### Manual Verification
- Execute `npx expo start` to test the mobile application using an iOS/Android simulator or a physical device.
- Verify user sign-in/sign-up flows and database persistence via Supabase Studio.
- Trigger an "anomalous" expense manually in the app and verify that the Isolation forest accurately flags it in the insights screen.
