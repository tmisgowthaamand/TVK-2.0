# TVK Connect 2.0 - System Architecture

This document provides a comprehensive overview of the system architecture for **TVK Connect 2.0**, a high-impact political command center and WhatsApp bot integration designed for real-time community intelligence.

---

## 1. High-Level Architecture Flow

TVK Connect 2.0 follows a modern decoupled architecture. The diagram below illustrates the high-level data flow and interactions between the frontend, backend, database, and external integrations.

```mermaid
flowchart TD
    User([Citizen/Volunteer]) -->|WhatsApp Messages| WABA[WhatsApp Business API]
    Admin([Command Center Admin]) -->|Browser| Frontend
    
    subgraph Client Layer
        Frontend[React Vite SPA - Frontend]
    end

    subgraph Backend Layer
        WABA <-->|Webhooks & REST API| FastAPI[FastAPI Backend - main.py]
        FastAPI <--> BotLogic[Bot Logic - bot_logic.py]
        FastAPI <--> FrontendAPI[Admin API Routes]
    end

    subgraph Data Layer
        FastAPI <-->|Async Motor| DB[(MongoDB Atlas)]
    end

    Frontend <-->|REST / Axios| FrontendAPI
```

---

## 2. Component Architecture

### 2.1. Frontend Architecture
The frontend is built with **React** and bundled using **Vite** for fast development and optimized production builds.

*   **Core Technologies:** React (v19), React Router (v7), Axios, Lucide React, SweetAlert2.
*   **Key Files:**
    *   `src/App.jsx`: Root component and routing.
    *   `src/AuthContext.jsx`: Authentication state.
    *   `src/Dashboard.jsx`: Vanguard Command Center interface (Bento Analytics grid).
    *   `src/LoginPage.jsx`: Secure entry point.

#### Frontend Data Flow Diagram
```mermaid
flowchart LR
    Admin([Admin User]) --> Login[LoginPage]
    Login -->|Authenticate| AuthContext
    AuthContext -->|Token| Dashboard[Dashboard]
    Dashboard -->|Fetch Analytics/Grievances| Axios[Axios HTTP Client]
    Axios -->|GET/POST| BackendAPI[FastAPI Backend]
    BackendAPI -->|JSON Response| Dashboard
    Dashboard -->|Update State| UI[Bento Analytics & Tables]
```

### 2.2. Backend Architecture
The backend is a robust asynchronous REST API and Bot Handler built on **FastAPI**.

*   **Core Technologies:** FastAPI, Uvicorn, Motor (MongoDB async), Pydantic, Requests.
*   **Key Modules:**
    *   `main.py`: Entry point, API routes, Webhooks.
    *   `bot_logic.py`: WhatsApp bot conversational state machine.
    *   `whatsapp.py`: WhatsApp Cloud API integration.
    *   `db.py`: MongoDB connection management.

#### Backend Flow Architecture
```mermaid
flowchart TD
    Request[Incoming Request] --> Router[main.py - Router/Middleware]
    
    Router -->|Admin Route| AdminService[Admin Services]
    Router -->|Webhook Route| WebhookService[WhatsApp Webhooks]
    
    AdminService --> DB[db.py - Motor]
    
    WebhookService --> Parse[Parse Message Intent]
    Parse --> BotLogic[bot_logic.py - State Machine]
    BotLogic --> DB
    BotLogic --> WAAPI[whatsapp.py - Send Message]
    WAAPI --> WAMeta[WhatsApp Cloud API]
```

### 2.3. Data Layer
*   **Database:** MongoDB Atlas.
*   **Driver:** `motor` for non-blocking database operations.
*   **Collections:** Users/Members, Grievances, Operations, Analytics.

---

## 3. WhatsApp Bot Architecture and Website Integration

The WhatsApp bot is the primary user interface for citizens and volunteers. It acts as an automated data collection agent that feeds directly into the Command Center website (Dashboard).

### 3.1. Full Bot Capabilities & Flows
The bot (`bot_logic.py`) handles complex conversational state machines for the following tasks:
1. **Voter Verification:** Authenticates users by matching their EPIC number (Voter ID) against the `voters_collection`. Unverified users are captured as guests pending approval.
2. **Grievance Reporting (FLOW1):** Citizens can report local issues by categorizing them (e.g., Water, Roads), providing text descriptions, uploading photos, and sharing live locations. Generates a unique `GRV` Reference ID and saves to `grievances_col`.
3. **Ideas & Suggestions (FLOW2):** Collects feedback and saves them with a `SUG` Reference ID into `member_requests_col`.
4. **Volunteer Registration (FLOW3):** Allows users to sign up for roles like "Booth Volunteer" or "Organise Meetings" (`VOL` Reference ID).
5. **Booth Pulse Polling (FLOW7):** A live voting system to capture the most pressing issue in a specific booth. Features a 30-minute cooldown and live result generation sent back as an image.
6. **Activity Tracking & Summary:** Users can track their grievance status using their Reference ID, or get an "Engagement Summary" detailing how many issues they have raised, resolved, and their volunteer status.
7. **Ward Connect & Networks:** Automatically links voters to their local Ward Coordinator by extracting their assigned booth number.

#### Internal Bot Sequence Diagram
```mermaid
sequenceDiagram
    participant Citizen
    participant WhatsApp API
    participant FastAPI (main.py)
    participant Bot Logic
    participant MongoDB
    
    Citizen->>WhatsApp API: "Hi" / Sends Message
    WhatsApp API->>FastAPI (main.py): POST /webhook (Message Event)
    FastAPI (main.py)->>Bot Logic: Parse intent & context
    Bot Logic->>MongoDB: Fetch current user state
    MongoDB-->>Bot Logic: State (e.g., "AWAITING_GRIEVANCE")
    Bot Logic->>MongoDB: Update state / Save grievance
    MongoDB-->>Bot Logic: Success
    Bot Logic->>FastAPI (main.py): Generate response payload
    FastAPI (main.py)->>WhatsApp API: POST message (Text/Interactive)
    WhatsApp API->>Citizen: Sends confirmation / next menu
```
### 3.2. Integration with the Command Center (Frontend Website)
The data collected by the bot does not sit idle; it is instantly pushed to the React SPA Dashboard used by Admins.

*   **Real-Time Data Sync:** Whenever the bot writes to MongoDB via the async `Motor` driver, the React frontend pulls this data via REST APIs to populate the **Bento Analytics** grid.
*   **Operational Strips (Grievance Tracking):** The frontend displays a live feed of all `GRV` and `PHT` (Photo Evidence) submissions. Admins can view the photos, locations, and descriptions submitted via WhatsApp.
*   **Status Control:** When an Admin on the website updates a grievance status from `Open` to `In Progress` or `Resolved`, the next time the citizen uses the bot to "Track My Issue", the bot queries the DB and reflects the Admin's change immediately.
*   **Booth Pulse Analytics:** The live voting done via the bot (`FLOW7`) populates the data visualization charts on the website's dashboard, giving Admins a bird's-eye view of constituency-wide concerns.

#### WhatsApp to Website Flow
```mermaid
sequenceDiagram
    participant Citizen
    participant WhatsApp Bot
    participant MongoDB
    participant React Dashboard
    participant Admin
    
    Citizen->>WhatsApp Bot: Submits Grievance + Photo
    WhatsApp Bot->>MongoDB: Saves Document (Status: Open)
    WhatsApp Bot->>Citizen: Sends Reference ID (e.g. GRV12345)
    
    React Dashboard->>MongoDB: Fetches new grievances
    MongoDB-->>React Dashboard: Returns new data
    React Dashboard->>Admin: Displays Grievance Card on screen
    
    Admin->>React Dashboard: Clicks "Resolve"
    React Dashboard->>MongoDB: Updates Status to "Resolved"
    
    Citizen->>WhatsApp Bot: "Track my Reference GRV12345"
    WhatsApp Bot->>MongoDB: Query status
    MongoDB-->>WhatsApp Bot: Status = Resolved
    WhatsApp Bot->>Citizen: Sends "Resolved" Status Report Image
```

---

## 4. Infrastructure & Deployment

*   **Frontend Deployment (Vercel):** Single Page Application, environment variables point to production API.
*   **Backend Deployment (Render):** Containerized via Docker (`Dockerfile`), configured with `render.yaml`.
*   **Data Layer:** Cloud-hosted MongoDB Atlas.

```mermaid
flowchart LR
    GitHub[GitHub Repo] -->|Push| Vercel[Vercel CI/CD]
    GitHub -->|Push| Render[Render CI/CD]
    
    Vercel -->|Deploys| ReactSPA[React Frontend]
    Render -->|Builds Docker| FastAPIContainer[FastAPI Backend Container]
    
    ReactSPA <-->|API Calls| FastAPIContainer
    FastAPIContainer <-->|Motor| MongoDB[(MongoDB Atlas)]
```
