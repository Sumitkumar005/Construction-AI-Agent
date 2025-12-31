"""Initialize vector database with sample construction specifications."""

import asyncio
import sys
import os
from pathlib import Path

# Change to backend directory to find .env file
backend_dir = Path(__file__).parent.parent
os.chdir(backend_dir)
sys.path.insert(0, str(backend_dir))

from src.rag.retrieval import RAGRetriever
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Initialize vector database."""
    logger.info("Initializing Qdrant vector database...")
    
    try:
        retriever = RAGRetriever()
        
        # Sample Division 8 specification content
        sample_specs = """
        DIVISION 8 - OPENINGS
        
        SECTION 08 11 00 - DOOR OPENINGS
        
        08 11 13 - METAL DOORS AND FRAMES
        Metal doors shall be constructed of steel with minimum 16-gauge face sheets.
        Door frames shall be steel, 16-gauge minimum, with anchors at 24 inches on center.
        Hardware preparation shall be provided for locksets, hinges, and closers.
        
        08 11 16 - WOOD DOORS
        Wood doors shall be solid core, minimum 1-3/4 inches thick.
        Doors shall be fire-rated where required by code.
        Hardware shall be mortised into door edge.
        
        SECTION 08 31 00 - WINDOWS
        
        08 31 13 - METAL WINDOWS
        Windows shall be aluminum frame, double-glazed, with thermal break.
        Minimum U-factor: 0.30.
        Operable windows shall have weatherstripping.
        
        SECTION 08 71 00 - DOOR HARDWARE
        
        08 71 13 - HARDWARE SCHEDULE
        Locksets: Grade 1, ANSI/BHMA A156.13.
        Hinges: Ball bearing, 4-1/2 inch x 4-1/2 inch, minimum 3 per door.
        Door closers: Surface mounted, adjustable.
        """
        
        # Add sample specs
        await retriever.add_specification_document(
            content=sample_specs,
            doc_id="division_8_sample",
            division="8",
            metadata={"source": "sample", "type": "specification"}
        )
        
        logger.info("✅ Vector database initialized successfully!")
        logger.info("✅ Sample Division 8 specifications added.")
        logger.info("\nYou can now use the RAG system to search for construction specifications!")
        
    except Exception as e:
        logger.error(f"❌ Error initializing vector database: {e}")
        logger.error("\nTroubleshooting:")
        logger.error("1. Check your Qdrant connection (run test_qdrant_connection.py)")
        logger.error("2. Verify QDRANT_URL and QDRANT_API_KEY in .env")
        raise


if __name__ == "__main__":
    asyncio.run(main())
