"""Initialize Qdrant vector database collection."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams

from app.core.config import get_settings

settings = get_settings()


async def initialize_qdrant():
    """Initialize Qdrant collection for embeddings."""
    print("🔍 Initializing Qdrant Vector Database...")
    print("=" * 50)

    try:
        # Create Qdrant client
        client = AsyncQdrantClient(
            host=settings.qdrant_host,
            port=settings.qdrant_port,
            api_key=settings.qdrant_api_key if hasattr(settings, 'qdrant_api_key') else None,
            https=settings.qdrant_use_ssl if hasattr(settings, 'qdrant_use_ssl') else False
        )

        print(f"📡 Connecting to Qdrant at {settings.qdrant_host}:{settings.qdrant_port}")

        # Check if collection exists
        collections = await client.get_collections()
        collection_names = [c.name for c in collections.collections]

        collection_name = getattr(settings, 'qdrant_collection_name', 'wisqu_embeddings')
        vector_size = getattr(settings, 'qdrant_vector_size', 768)

        if collection_name in collection_names:
            print(f"✅ Collection '{collection_name}' already exists")

            # Get collection info
            collection_info = await client.get_collection(collection_name)
            print(f"   Vectors: {collection_info.vectors_count}")
            print(f"   Points: {collection_info.points_count}")
            return

        # Create collection
        print(f"📦 Creating collection: {collection_name}")
        print(f"   Vector size: {vector_size}")
        print(f"   Distance metric: COSINE")

        await client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE
            )
        )

        print(f"✅ Collection '{collection_name}' created successfully!")

    except Exception as e:
        print(f"❌ Error initializing Qdrant: {e}")
        print()
        print("Troubleshooting:")
        print("1. Check QDRANT_HOST and QDRANT_PORT in .env")
        print("2. Verify Qdrant is running: docker ps | grep qdrant")
        print("3. Test connection: curl http://{host}:{port}/collections")
        raise

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(initialize_qdrant())
