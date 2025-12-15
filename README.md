# Autonomous Contract Comparison and Change Extraction Agent

## Project Description

The Autonomous Contract Comparison and Change Extraction Agent is an AI-powered system designed to automate the labor-intensive process of comparing legal contracts and identifying changes introduced in amendments. This system addresses a critical pain point in legal technology: legal compliance teams currently spend 40+ hours per week manually comparing original contracts with their amendments to identify changes, assess impact, and route documents for appropriate review. This manual process is error-prone, slow, and prevents teams from scaling to handle growing contract volumes.

The system leverages state-of-the-art multimodal large language models (GPT-4o via OpenRouter) to parse scanned contract images directly, eliminating the need for manual OCR preprocessing. It employs a sophisticated two-agent collaborative architecture that mimics how legal analysts work: first understanding the document context and structure, then identifying and extracting specific changes. The system returns structured, Pydantic-validated outputs that can be seamlessly integrated into downstream legal systems such as compliance dashboards, review queues, and legal databases.

Complete observability is built into the system through Langfuse integration, capturing every step of the workflow including image parsing, agent execution, handoffs, and validation. This enables debugging misclassifications, identifying performance bottlenecks, and conducting cost analysis for production deployment. The system represents a production-ready solution that demonstrates mastery of multimodal document processing, agent collaboration, structured validation, and production observability—skills essential for high-impact AI engineering roles in legal technology.

## Architecture

The system follows a multi-stage pipeline architecture that processes contract images through sequential stages of analysis and extraction:

**Stage 1: Image Parsing** - The workflow begins with the `ImageParser` module, which validates input images (checking format, size, and existence), encodes them to base64, and makes multimodal API calls to GPT-4o via OpenRouter. The vision-specific prompts are tailored for contract parsing, instructing the model to preserve document hierarchy, section numbers, and formatting cues.

**Stage 2: Agent 1 - Contextualization** - The `ContextualizationAgent` receives both the original and amended contract texts. This agent analyzes the overall document structure, identifies sections and subsections, maps corresponding sections between documents, and identifies key legal domains covered (e.g., payment terms, liability, intellectual property). This contextualization output provides crucial context for the next stage.

**Stage 3: Agent 2 - Change Extraction** - The `ExtractionAgent` receives Agent 1's contextualization output along with both contract texts. Using the structural understanding from Agent 1, Agent 2 performs precise change extraction, identifying modified sections, affected topics, and generating comprehensive summaries. The agent uses JSON mode to ensure structured output.

**Stage 4: Validation** - The extracted changes are validated using Pydantic models (`ContractChangeOutput`), which enforce field constraints (minimum lengths, non-empty lists), type hints, and custom validators. This ensures data integrity and prevents malformed outputs from breaking downstream integrations.

**Stage 5: Tracing & Output** - Throughout the workflow, Langfuse captures traces for each operation, including input/output data, latency, token usage, and costs. Custom metadata (session_id, contract_id, agent names) is attached to all traces. The final validated output is returned as structured JSON.

The handoff mechanism between agents is explicit: Agent 1's output dictionary is passed directly to Agent 2's `extract_changes` method, ensuring clear data flow and traceability. All components are instrumented with Langfuse tracing, providing complete observability into the system's behavior.

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- OpenAI API key (via OpenRouter)
- Langfuse account and API keys

### Installation

1. **Clone the repository** (if applicable) or navigate to the project directory:
   ```bash
   cd assignment_4
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   - Copy `.env.example` to `.env` (or create `.env` manually)
   - Fill in your API keys:
     ```
     OPENAI_API_KEY=your-openrouter-api-key-here
     LANGFUSE_PUBLIC_KEY=pk-lf-your-public-key
     LANGFUSE_SECRET_KEY=sk-lf-your-secret-key
     LANGFUSE_HOST=https://cloud.langfuse.com
     ```

5. **Prepare test images**:
   - Place your contract images in `data/test_contracts/`
   - Ensure you have at least 2 contract pairs (4 images total)
   - See `data/test_contracts/README.md` for details

## Usage

### Basic Usage

Run the contract comparison agent from the command line:

```bash
python src/main.py <original_contract_image> <amended_contract_image>
```

### Example Command

```bash
python src/main.py data/test_contracts/pair1_original.png data/test_contracts/pair1_amendment.png
```

### Advanced Options

```bash
# Save output to a file
python src/main.py original.jpg amendment.jpg --output results.json

# Specify custom session and contract IDs for tracing
python src/main.py original.jpg amendment.jpg --session-id "session_123" --contract-id "contract_456"
```

### Command Line Arguments

- `original_image`: Path to the original contract image file (required)
- `amendment_image`: Path to the amended contract image file (required)
- `--output`, `-o`: Output file path for JSON results (optional, defaults to stdout)
- `--session-id`: Custom session ID for tracing (optional, auto-generated if not provided)
- `--contract-id`: Custom contract ID for tracing (optional, auto-generated if not provided)

## Expected Output Format

The system returns a structured JSON object with the following format:

```json
{
  "sections_changed": [
    "Section 3: Payment Terms",
    "Section 7: Termination Clause"
  ],
  "topics_touched": [
    "Payment Schedule",
    "Liability",
    "Termination Rights"
  ],
  "summary_of_the_change": "The payment terms were extended from 30 to 45 days, and a new termination clause was added allowing either party to terminate with 60 days notice.",
  "metadata": {
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "contract_id": "660e8400-e29b-41d4-a716-446655440001",
    "original_image": "data/test_contracts/pair1_original.png",
    "amendment_image": "data/test_contracts/pair1_amendment.png"
  }
}
```

### Output Fields

- **sections_changed**: List of section names or identifiers that were modified (minimum 1 required)
- **topics_touched**: List of topics or subject areas affected by the changes (minimum 1 required)
- **summary_of_the_change**: Comprehensive summary of all changes (minimum 50 characters required)
- **metadata**: Additional information including session ID, contract ID, and input file paths

## Technical Decisions

### Why Two Agents?

The two-agent architecture was chosen to mimic the natural workflow of legal analysts, who first understand document context before identifying specific changes. This separation of concerns provides several benefits:

1. **Improved Accuracy**: Agent 1's contextualization helps Agent 2 understand document structure, reducing false positives from structural differences (e.g., renumbering) versus actual content changes.

2. **Better Prompt Engineering**: Each agent can have specialized prompts optimized for its specific task, rather than trying to accomplish both tasks in a single prompt.

3. **Traceability**: The explicit handoff between agents makes it easier to debug issues—if Agent 2 produces incorrect results, we can inspect Agent 1's contextualization to identify the root cause.

4. **Scalability**: This architecture allows for future enhancements, such as adding specialized agents for different types of changes (financial terms, legal clauses, etc.).

### Why GPT-4o via OpenRouter?

GPT-4o was selected for several reasons:

1. **Multimodal Capabilities**: GPT-4o provides excellent vision capabilities for parsing scanned documents, handling varying image qualities and formats.

2. **OpenRouter Integration**: Using OpenRouter provides flexibility to switch models if needed and often offers competitive pricing. It also simplifies API key management.

3. **JSON Mode Support**: GPT-4o supports structured output via JSON mode, which is crucial for Agent 2's change extraction task.

4. **Performance**: GPT-4o demonstrates strong performance on document understanding tasks, with good accuracy in preserving document structure and hierarchy.

### Prompt Engineering Strategy

The prompts are designed with specific strategies:

1. **Low Temperature (0.1-0.2)**: Ensures consistent, deterministic outputs critical for legal document analysis.

2. **Structured Instructions**: Clear, numbered instructions help the model follow the desired workflow.

3. **Context Preservation**: Vision prompts explicitly instruct the model to preserve document hierarchy and structure.

4. **JSON Enforcement**: Agent 2 uses JSON mode to guarantee structured output, which is then validated by Pydantic.

### Pydantic Validation

Pydantic models provide runtime validation that ensures data integrity before outputs reach downstream systems. Custom validators enforce business logic (e.g., minimum summary length) and field constraints, preventing malformed data from breaking integrations.

## Langfuse Tracing Guide

Langfuse integration provides complete observability into the contract comparison workflow. To view traces:

1. **Access the Langfuse Dashboard**: Navigate to your Langfuse host URL (default: https://cloud.langfuse.com) and log in with your credentials.

2. **View Traces**: In the dashboard, navigate to the "Traces" section. You'll see traces for:
   - `image_parsing_original` and `image_parsing_amendment`: Image parsing operations
   - `agent_1_contextualization`: Agent 1's document analysis
   - `agent_2_extraction`: Agent 2's change extraction
   - `contract_comparison_workflow`: Main workflow trace containing all operations

3. **Trace Details**: Click on any trace to view:
   - **Input/Output**: The data passed to and returned from each operation
   - **Latency**: Time taken for each operation
   - **Tokens**: Token usage (prompt and completion tokens)
   - **Cost**: Estimated cost based on token usage
   - **Metadata**: Custom metadata including session_id, contract_id, and agent names

4. **Filtering**: Use the search and filter options to find traces by:
   - Session ID
   - Contract ID
   - Agent name
   - Date range

5. **Scoring**: Traces are automatically scored (workflow_success, extraction_quality, etc.) to help identify successful vs. failed operations.

6. **Debugging**: When issues occur, inspect the trace hierarchy to identify which stage failed, review the input/output data, and analyze error messages logged in the trace spans.

## Running Tests

The project includes comprehensive test suites covering validation, agent handoff, image parsing, and end-to-end integration.

### Run All Tests

```bash
pytest tests/
```

### Run Specific Test Suites

```bash
# Pydantic validation tests
pytest tests/test_validation.py

# Agent handoff tests
pytest tests/test_agents.py

# Image parsing tests
pytest tests/test_image_parser.py

# End-to-end integration tests
pytest tests/test_integration.py
```

### Test Coverage

The test suite includes:

1. **Pydantic Validation Test** (`test_validation.py`): Tests both valid and invalid outputs, ensuring the model correctly validates data.

2. **Agent Handoff Test** (`test_agents.py`): Verifies that Agent 2 correctly receives and uses Agent 1's contextualization output.

3. **Image Parsing Test** (`test_image_parser.py`): Tests image validation, encoding, and parsing functionality.

4. **Integration Test** (`test_integration.py`): End-to-end test of the complete workflow from image parsing through change extraction.

### Test Requirements

Tests use `pytest` and `unittest.mock` for mocking API calls. Install test dependencies:

```bash
pip install pytest pytest-mock
```

## Project Structure

```
assignment_4/
├── src/
│   ├── __init__.py
│   ├── main.py                 # Main application entry point
│   ├── models.py               # Pydantic models for validation
│   ├── image_parser.py         # Image processing utilities
│   ├── tracing.py              # Langfuse tracing utilities
│   └── agents/
│       ├── __init__.py
│       ├── contextualization_agent.py  # Agent 1: Document contextualization
│       └── extraction_agent.py         # Agent 2: Change extraction
├── tests/
│   ├── __init__.py
│   ├── test_validation.py      # Pydantic validation tests
│   ├── test_agents.py          # Agent handoff tests
│   ├── test_image_parser.py    # Image parsing tests
│   └── test_integration.py     # End-to-end integration tests
├── data/
│   └── test_contracts/
│       ├── README.md           # Test contract documentation
│       └── [test images]       # Contract image pairs
├── requirements.txt            # Python dependencies
├── .env.example               # Environment variable template
└── README.md                  # This file
```

## License

This project is developed for educational purposes as part of an AI engineering training program.

## Support

For issues or questions, please refer to the test documentation in `data/test_contracts/README.md` or review the test files for usage examples.
