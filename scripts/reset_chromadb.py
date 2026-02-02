
"""
Reset ChromaDB Script
Deletes the ChromaDB vector database and recreates it empty.
WARNING: This will delete ALL KB embeddings!
"""

import os
import sys
import shutil

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def reset_chromadb():
    """Delete ChromaDB directory and recreate empty"""
    
    print("=" * 60)
    print("CHROMADB RESET SCRIPT")
    print("=" * 60)
    print("\n⚠️  WARNING: This will DELETE ALL embeddings in ChromaDB!")
    
    # ChromaDB path
    chroma_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'kb', 'chroma_db'
    )
    
    print(f"ChromaDB Path: {chroma_path}")
    print()
    
    # Check if directory exists
    if not os.path.exists(chroma_path):
        print("ℹ️  ChromaDB directory does not exist. Nothing to reset.")
        return True
    
    # Show contents
    print("Current contents:")
    for item in os.listdir(chroma_path):
        item_path = os.path.join(chroma_path, item)
        if os.path.isdir(item_path):
            print(f"   📁 {item}/")
        else:
            size = os.path.getsize(item_path)
            print(f"   📄 {item} ({size:,} bytes)")
    print()
    
    # Confirm action
    confirm = input("Type 'RESET' to confirm: ")
    if confirm != 'RESET':
        print("❌ Aborted. No changes made.")
        return False
    
    try:
        # Delete directory
        print("\n🗑️  Deleting ChromaDB directory...")
        shutil.rmtree(chroma_path)
        print(f"   ✓ Deleted {chroma_path}")
        
        # Recreate empty directory
        print("📁 Creating empty ChromaDB directory...")
        os.makedirs(chroma_path, exist_ok=True)
        print(f"   ✓ Created {chroma_path}")
        
        # Create .gitkeep
        gitkeep_path = os.path.join(chroma_path, '.gitkeep')
        with open(gitkeep_path, 'w') as f:
            f.write('')
        print(f"   ✓ Created .gitkeep")
        
        print("\n" + "=" * 60)
        print("✅ CHROMADB RESET COMPLETE!")
        print("=" * 60)
        print("\nNext steps:")
        print("  Run: python scripts/populate_kb.py")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return False


if __name__ == '__main__':
    success = reset_chromadb()
    sys.exit(0 if success else 1)
