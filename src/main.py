"""
Main application script for Autonomous Contract Comparison and Change Extraction Agent.
Entry point that orchestrates the entire workflow.
"""
import argparse
import json
import sys
import uuid
from pathlib import Path

# Add project root to Python path to enable imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.image_parser import ImageParser
from src.agents.contextualization_agent import ContextualizationAgent
from src.agents.extraction_agent import ExtractionAgent
from src.models import ContractChangeOutput
from src.tracing import tracing_manager


def main():
    """
    Main entry point for the contract comparison agent.
    Orchestrates the complete workflow:
    1. Parse command line arguments
    2. Parse both images using multimodal LLM
    3. Execute Agent 1 (contextualization)
    4. Execute Agent 2 (change extraction)
    5. Validate output using Pydantic
    6. Return structured JSON
    """
    parser = argparse.ArgumentParser(
        description="Autonomous Contract Comparison and Change Extraction Agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example usage:
  python src/main.py original_contract.jpg amended_contract.jpg
  
  python src/main.py data/test_contracts/pair1_original.png data/test_contracts/pair1_amendment.png
        """
    )
    
    parser.add_argument(
        "original_image",
        type=str,
        help="Path to the original contract image file"
    )
    
    parser.add_argument(
        "amendment_image",
        type=str,
        help="Path to the amended contract image file"
    )
    
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Output file path for JSON results (default: print to stdout)"
    )
    
    parser.add_argument(
        "--session-id",
        type=str,
        default=None,
        help="Custom session ID for tracing (default: auto-generated)"
    )
    
    parser.add_argument(
        "--contract-id",
        type=str,
        default=None,
        help="Custom contract ID for tracing (default: auto-generated)"
    )
    
    args = parser.parse_args()
    
    # Generate IDs for tracing
    session_id = args.session_id or str(uuid.uuid4())
    contract_id = args.contract_id or str(uuid.uuid4())
    
    # Create main workflow trace
    main_trace = tracing_manager.create_trace(
        name="contract_comparison_workflow",
        session_id=session_id,
        contract_id=contract_id,
        metadata={
            "original_image": args.original_image,
            "amendment_image": args.amendment_image
        }
    )
    
    try:
        # Step 1: Parse both images using multimodal LLM
        print("Step 1: Parsing contract images...")
        image_parser = ImageParser()
        
        original_text = image_parser.parse_image(
            image_path=args.original_image,
            session_id=session_id,
            contract_id=contract_id,
            document_type="original"
        )
        
        amendment_text = image_parser.parse_image(
            image_path=args.amendment_image,
            session_id=session_id,
            contract_id=contract_id,
            document_type="amendment"
        )
        
        main_trace.span(
            name="image_parsing_complete",
            input={"original_path": args.original_image, "amendment_path": args.amendment_image},
            output={"original_length": len(original_text), "amendment_length": len(amendment_text)}
        )
        
        print(f"✓ Parsed original contract: {len(original_text)} characters")
        print(f"✓ Parsed amended contract: {len(amendment_text)} characters")
        
        # Step 2: Execute Agent 1 (Contextualization)
        print("\nStep 2: Executing Agent 1 (Contextualization)...")
        contextualization_agent = ContextualizationAgent()
        
        contextualization_output = contextualization_agent.analyze_documents(
            original_text=original_text,
            amendment_text=amendment_text,
            session_id=session_id,
            contract_id=contract_id
        )
        
        main_trace.span(
            name="agent_1_complete",
            input={"original_length": len(original_text), "amendment_length": len(amendment_text)},
            output={"analysis_length": len(contextualization_output.get("analysis", ""))}
        )
        
        print("✓ Agent 1 completed contextualization analysis")
        
        # Step 3: Execute Agent 2 (Change Extraction)
        print("\nStep 3: Executing Agent 2 (Change Extraction)...")
        extraction_agent = ExtractionAgent()
        
        change_output = extraction_agent.extract_changes(
            original_text=original_text,
            amendment_text=amendment_text,
            contextualization_output=contextualization_output,
            session_id=session_id,
            contract_id=contract_id
        )
        
        main_trace.span(
            name="agent_2_complete",
            input={"has_contextualization": True},
            output={
                "sections_changed_count": len(change_output.sections_changed),
                "topics_touched_count": len(change_output.topics_touched)
            }
        )
        
        print("✓ Agent 2 completed change extraction")
        
        # Step 4: Validate output (already validated by Pydantic in Agent 2)
        print("\nStep 4: Validating output...")
        # Validation is implicit through Pydantic model instantiation
        main_trace.span(
            name="validation_complete",
            input={"output_type": "ContractChangeOutput"},
            output={"validated": True}
        )
        
        print("✓ Output validated successfully")
        
        # Step 5: Return structured JSON
        result = change_output.model_dump()
        
        # Add metadata
        result["metadata"] = {
            "session_id": session_id,
            "contract_id": contract_id,
            "original_image": args.original_image,
            "amendment_image": args.amendment_image
        }
        
        # Format JSON output
        json_output = json.dumps(result, indent=2, ensure_ascii=False)
        
        # Write to file or stdout
        if args.output:
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(json_output)
            print(f"\n✓ Results saved to: {args.output}")
        else:
            print("\n" + "="*60)
            print("EXTRACTION RESULTS")
            print("="*60)
            print(json_output)
        
        # Score the main trace
        main_trace.score(name="workflow_success", value=1.0)
        
        return 0
        
    except Exception as e:
        # Log error to trace
        main_trace.span(
            name="workflow_error",
            input={"original_image": args.original_image, "amendment_image": args.amendment_image},
            output={"error": str(e)},
            level="ERROR"
        )
        main_trace.score(name="workflow_success", value=0.0)
        
        print(f"\n✗ Error: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
