"""
Populate Knowledge Base Script
Loads KB data from initial_kb.json into both ChromaDB and PostgreSQL.
"""

import os
import sys
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kb.kb_chroma import KnowledgeBase
from db.postgres import PostgresDB


def populate_kb():
    """Populate knowledge base from JSON file"""
    
    print("=" * 60)
    print("POPULATE KNOWLEDGE BASE SCRIPT")
    print("=" * 60)
    
    # Paths
    kb_json_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'kb', 'data', 'initial_kb.json'
    )
    
    print(f"\n📄 KB JSON Path: {kb_json_path}")
    
    # Check if file exists
    if not os.path.exists(kb_json_path):
        print(f"❌ KB file not found: {kb_json_path}")
        return False
    
    try:
        # Load JSON
        print("\n📖 Loading KB data from JSON...")
        with open(kb_json_path, 'r', encoding='utf-8') as f:
            kb_data = json.load(f)
        
        categories = kb_data.get('categories', [])
        print(f"   Found {len(categories)} categories")
        
        total_articles = 0
        for cat in categories:
            total_articles += len(cat.get('subcategories', []))
        print(f"   Found {total_articles} total articles")
        
        # Initialize Database (PostgreSQL) first
        print("\n🔄 Initializing PostgreSQL connection...")
        db = PostgresDB()
        
        # Clear existing KB data in PostgreSQL
        print("🗑️  Clearing existing PostgreSQL KB entries...")
        try:
            db.execute_query("DELETE FROM knowledge_articles")
            db.execute_query("DELETE FROM kb_categories")
            print("   ✓ Cleared PostgreSQL KB tables")
        except Exception as e:
            print(f"   ⚠ Warning: {e}")
        
        # Insert categories into PostgreSQL
        print("\n📝 Inserting categories into PostgreSQL...")
        for cat in categories:
            try:
                db.execute_query("""
                    INSERT INTO kb_categories (id, name, display_name, icon)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        display_name = EXCLUDED.display_name,
                        icon = EXCLUDED.icon
                """, (
                    cat['id'],
                    cat['name'],
                    cat.get('display_name', cat['name']),
                    cat.get('icon', '📋')
                ))
                print(f"   ✓ Category: {cat['name']}")
            except Exception as e:
                print(f"   ⚠ Error with category {cat['name']}: {e}")
        
        # Initialize KB (ChromaDB)
        print("\n🔄 Initializing ChromaDB...")
        kb = KnowledgeBase()
        
        # Insert articles
        print("\n📝 Inserting articles...")
        chromadb_count = 0
        postgres_count = 0
        
        for cat in categories:
            cat_id = cat['id']
            cat_name = cat['name']
            
            for subcat in cat.get('subcategories', []):
                subcat_id = subcat['id']
                title = subcat['title']
                solution = subcat['solution']
                keywords = subcat.get('keywords', [])
                source = subcat.get('source', 'IT Documentation')
                
                # Insert into ChromaDB
                try:
                    kb.add_entry(
                        issue=title,
                        solution=solution,
                        source=source,
                        entry_id=subcat_id,
                        category=cat_name,
                        subcategory=subcat_id,
                        keywords=keywords
                    )
                    chromadb_count += 1
                except Exception as e:
                    print(f"   ⚠ ChromaDB error for {subcat_id}: {e}")
                
                # Insert into PostgreSQL
                try:
                    # Keywords as PostgreSQL array
                    keywords_array = keywords if keywords else None
                    db.execute_query("""
                        INSERT INTO knowledge_articles 
                        (id, title, category, subcategory, solution, keywords, source, author)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            title = EXCLUDED.title,
                            category = EXCLUDED.category,
                            subcategory = EXCLUDED.subcategory,
                            solution = EXCLUDED.solution,
                            keywords = EXCLUDED.keywords,
                            source = EXCLUDED.source,
                            updated_at = CURRENT_TIMESTAMP
                    """, (
                        subcat_id,
                        title,
                        cat_name,
                        subcat_id,
                        solution,
                        keywords_array,
                        source,
                        'System'
                    ))
                    postgres_count += 1
                except Exception as e:
                    print(f"   ⚠ PostgreSQL error for {subcat_id}: {e}")
        
        print(f"\n   ✓ Inserted {chromadb_count} entries into ChromaDB")
        print(f"   ✓ Inserted {postgres_count} entries into PostgreSQL")
        
        # Verify
        print("\n🔍 Verifying...")
        
        # ChromaDB stats
        try:
            stats = kb.get_stats()
            print(f"   ChromaDB entries: {stats.get('total_entries', 'N/A')}")
        except Exception as e:
            print(f"   ChromaDB stats: Unable to retrieve ({e})")
        
        # PostgreSQL stats
        result = db.execute_query("SELECT COUNT(*) as cnt FROM knowledge_articles", fetch=True)
        pg_count = result[0]['cnt'] if result else 0
        print(f"   PostgreSQL articles: {pg_count}")
        
        result = db.execute_query("SELECT COUNT(*) as cnt FROM kb_categories", fetch=True)
        cat_count = result[0]['cnt'] if result else 0
        print(f"   PostgreSQL categories: {cat_count}")
        
        print("\n" + "=" * 60)
        print("✅ KNOWLEDGE BASE POPULATED SUCCESSFULLY!")
        print("=" * 60)
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"\n❌ JSON parse error: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = populate_kb()
    sys.exit(0 if success else 1)
