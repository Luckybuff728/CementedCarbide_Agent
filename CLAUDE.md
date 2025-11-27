# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Essential Development Commands

### Docker Production Deployment (Recommended)
```bash
# Build and start all services
docker-compose build
docker-compose up -d

# View logs
docker-compose logs -f                    # All services
docker-compose logs -f backend           # Backend only
docker-compose logs -f frontend          # Frontend only

# Service management
docker-compose ps                         # Check status
docker-compose restart                   # Restart services
docker-compose down                      # Stop services

# Access containers
docker exec -it topmat-backend bash      # Backend shell
docker exec -it topmat-frontend sh       # Frontend shell (alpine)
```

### Local Development Setup
```bash
# Backend (Python 3.11+)
pip install -r requirements.txt
python run.py                            # Choose option 1 for FastAPI

# Frontend (Node.js 20+)
cd frontend
npm install
npm run dev                              # Development server on :5173
npm run build                            # Production build

# Environment setup
cp .env.example .env                     # Configure DASHSCOPE_API_KEY
```

### Testing and Validation
```bash
# Run backend tests
python run.py                            # Choose option 3 for tests
pytest tests/ -v

# Frontend linting (if configured)
cd frontend && npm run lint
```

## System Architecture

### High-Level Design
TopMat Agent is a **LangGraph-based coating optimization system** that provides intelligent recommendations for hard alloy coatings through a 12-node workflow engine.

**Architecture Pattern**: Frontend (Vue 3) ↔ WebSocket ↔ Backend (FastAPI + LangGraph)

### Frontend Architecture
- **Framework**: Vue 3 with Composition API
- **State Management**: Pinia store (`useWorkflowStore`)
- **Real-time Communication**: Native WebSocket with custom message protocol
- **UI Layout**: Three-panel resizable layout (Left: Form | Center: Workflow | Right: Results)
- **Key Features**: Real-time streaming output, markdown rendering, session management

**Core Components**:
- `App.vue` - Main application with WebSocket message handling
- `stores/workflow.js` - Central state management for workflow execution
- `composables/useWebSocket.js` - WebSocket communication abstraction
- `components/CenterPanel.vue` - Workflow step visualization with scroll-to-node

### Backend Architecture
- **API Framework**: FastAPI with modular routing
- **Workflow Engine**: LangGraph StateGraph with 12 optimized nodes
- **Service Layer**: ValidationService, OptimizationService, CoatingService
- **LLM Integration**: Qwen model via DashScope API

**Core Modules**:
- `src/graph/workflow.py` - Main workflow orchestration with `CoatingWorkflowManager`
- `src/graph/state.py` - `CoatingWorkflowState` TypedDict for workflow state
- `src/graph/nodes.py` - Individual workflow node implementations
- `src/api/main.py` - FastAPI application with CORS and error handling

## LangGraph Workflow System

### Workflow Pipeline (12 Nodes)
The coating optimization follows this sequence:

1. **input_validation** - Validates coating composition, process params, structure design
2. **topphi_simulation** - First-principles simulation (currently mocked)
3. **ml_prediction** - Machine learning performance prediction
4. **historical_comparison** - Historical data matching and comparison
5. **integrated_analysis** - Root cause analysis and confidence scoring
6. **p1_composition_optimization** - Composition optimization suggestions (parallel)
7. **p2_structure_optimization** - Structure optimization suggestions (parallel)
8. **p3_process_optimization** - Process optimization suggestions (parallel)
9. **optimization_summary** - Consolidates P1/P2/P3 recommendations
10. **experiment_workorder_generation** - Creates detailed experimental workorder
11. **experiment_result_analysis** - Analyzes user-provided experiment results
12. **decide_next_iteration** - Determines if optimization is complete

### Execution Pattern
- **Sequential Phase**: Nodes 1-5 execute sequentially for performance prediction
- **Parallel Phase**: Nodes 6-8 execute in parallel for P1/P2/P3 optimization
- **User Interaction**: System waits for user to select optimization plan before continuing
- **Iterative Loop**: Can iterate multiple times based on experiment results

### State Management
The `CoatingWorkflowState` tracks:
- Input parameters (composition, process_params, structure_design)
- Prediction results (topphi_simulation, ml_prediction, historical_comparison)
- Optimization suggestions (p1_suggestions, p2_suggestions, p3_suggestions)
- Iteration metadata (current_iteration, experiment_results)

## WebSocket Communication Protocol

### Message Types
```javascript
// Client to Server
{
  "type": "start_workflow",
  "data": { /* coating input parameters */ }
}

{
  "type": "generate_workorder",
  "selected_option": "P1" | "P2" | "P3"
}

{
  "type": "submit_experiment_results",
  "data": { /* experiment measurement data */ }
}

// Server to Client
{
  "type": "node_output",
  "data": { "node_name": { /* node execution results */ } }
}

{
  "type": "llm_stream",
  "node": "node_name",
  "content": "partial LLM response..."
}

{
  "type": "workflow_completed",
  "data": { /* final workflow state */ }
}
```

### Frontend Message Handling
In `App.vue`, the `handleWebSocketMessage` function processes:
- **node_output**: Updates workflow state and marks nodes as completed
- **llm_stream**: Provides real-time typewriter effect for LLM responses
- **workflow_completed**: Shows optimization selection interface

## Service Layer Architecture

### ValidationService (`src/services/validation_service.py`)
- Validates coating composition ranges (Al: 5-40%, Ti: 5-35%, N: 30-70%)
- Checks process parameter constraints
- Provides structured error messages

### OptimizationService (`src/services/optimization_service.py`)
- Generates P1/P2/P3 optimization suggestions using LLM
- Handles structured content formatting
- Manages suggestion ranking and filtering

### CoatingService (`src/services/coating_service.py`)
- Core business logic orchestration
- Coordinates between validation, optimization, and analysis
- Handles data persistence and retrieval

## Key Configuration

### Environment Variables (.env)
```bash
DASHSCOPE_API_KEY=your_api_key_here    # Required for LLM integration
DASHSCOPE_MODEL_NAME=qwen-plus          # Model selection
SERVER_HOST=0.0.0.0                     # Backend bind address
SERVER_PORT=8000                        # Backend port
LOG_LEVEL=info                          # Logging verbosity
```

### Docker Configuration
- **Frontend**: Multi-stage build (Node.js 20 builder → Nginx alpine runtime)
- **Backend**: Python 3.11 slim with uvicorn multi-worker (4 processes)
- **Network**: Custom bridge network (172.28.0.0/16)
- **Resource limits**: Backend 2GB RAM, Frontend 256MB RAM

### Port Mapping
- **Production**: Frontend :8081 → Nginx :80 (reverse proxy to backend :8000)
- **Development**: Frontend :5173 (Vite), Backend :8000 (FastAPI)

## Development Patterns

### Adding New Workflow Nodes
1. Define node function in `src/graph/nodes.py`
2. Add node to workflow in `src/graph/workflow.py`
3. Update `CoatingWorkflowState` if new state fields needed
4. Handle node output in frontend `handleNodeOutput` function

### Frontend State Updates
- Use `workflowStore.addProcessStep()` for new workflow steps
- Store node-specific data in dedicated store fields (e.g., `performancePrediction`)
- P1/P2/P3 content is stored separately to avoid parallel execution conflicts

### WebSocket Extensions
- Add new message types to `handleWebSocketMessage` in `App.vue`
- Server-side: emit messages through WebSocket connection in route handlers
- Use structured message format with `type` and `data` fields

### Service Integration
- Follow dependency injection pattern in service constructors
- Use structured error handling with custom exceptions
- Implement async/await pattern for all service methods

## Important Implementation Notes

### Node Execution Order Matters
The workflow relies on specific execution order. Performance prediction nodes (1-5) must complete before optimization nodes (6-8) can begin.

### P1/P2/P3 Parallel Handling
The three optimization nodes execute in parallel but their content is stored separately (`p1Content`, `p2Content`, `p3Content`) to prevent race conditions in the frontend.

### WebSocket Connection Management
- Frontend automatically reconnects on connection loss
- Backend handles connection lifecycle through FastAPI WebSocket endpoints
- Connection state is reflected in UI through status indicators

### State Persistence
- Workflow state is maintained in memory during session
- Future enhancement: Add database persistence for long-term storage
- Current session data is lost on server restart

### Error Handling Strategy
- Validation errors are returned immediately with specific field guidance
- Workflow execution errors are captured and returned through WebSocket
- Frontend displays errors in user-friendly format with retry options