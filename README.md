# Climate-Aware Supply Chain Multi-Agent System

## Overview

This project is a Proof of Concept (PoC) demonstrating a **multi-agent system** that leverages **IBM watsonx.ai** and **Retrieval-Augmented Generation (RAG)** to provide climate-aware risk analysis 
for supply chain locations. 
It enables businesses to make informed decisions by assessing weather risks and historical climate data relevant to key supply chain points.

---

## Features

- **Multi-agent architecture** with specialized agents for:
  - Location intelligence
  - Climate data retrieval
  - Business risk analysis
  - Orchestrator agent to coordinate tasks
- Integration with **IBM watsonx.ai** for advanced AI-driven chat and recommendations.
- **Retrieval-Augmented Generation (RAG)** to access and use historical climate data and previous location history for context-aware insights.
- Interactive web interface:
  - Chat panel for querying weather, supply risks, and advice.
  - Map component for selecting locations globally.
- Backend API to handle communication between frontend and agents.

---

## Tech Stack

- **Frontend:** React.js  
- **Backend:**  Flask  
- **AI & NLP:** IBM watsonx.ai  
- **Data Retrieval:** RAG framework  
- **Map Integration:** React map component with location picker  
- **HTTP Client:** Axios   

---

## Setup & Installation

1. Clone the repository:  
   ```bash
   git clone https://github.com/meathul/Watsonx-challenge.git
2. Run the Frontend:
   '''bash
   npm run dev
3.Run the backend:
  '''bash
  python main.py


   

