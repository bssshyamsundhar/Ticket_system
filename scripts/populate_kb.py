"""
Populate Knowledge Base Script
Loads KB data from data.json (hierarchical IT support data) into both ChromaDB and PostgreSQL.
Replaces all existing embeddings from initial_kb.json.
"""

import os
import sys
import json

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kb.kb_chroma import KnowledgeBase
from db.postgres import PostgresDB


def flatten_data_json(data):
    """
    Flatten the hierarchical data.json into a list of issue entries.
    
    Structure: { ticket_type: { smart_category: { category: { type: { item: [ {issue, bot_solution} ] } } } } }
    
    Returns list of dicts with: issue, bot_solution, ticket_type, smart_category, category, type, item, entry_id
    """
    entries = []
    counter = 0
    
    for ticket_type, smart_categories in data.items():
        if not isinstance(smart_categories, dict):
            continue
        for smart_category, categories in smart_categories.items():
            if not isinstance(categories, dict):
                continue
            for category, types in categories.items():
                if not isinstance(types, dict):
                    continue
                for type_name, items in types.items():
                    if not isinstance(items, dict):
                        continue
                    for item_name, issues in items.items():
                        if not isinstance(issues, list):
                            continue
                        for idx, issue_obj in enumerate(issues):
                            if not isinstance(issue_obj, dict):
                                continue
                            issue_text = issue_obj.get('issue', '').strip()
                            bot_solution = issue_obj.get('bot_solution', '').strip()
                            if not issue_text or not bot_solution:
                                continue
                            
                            counter += 1
                            entry_id = f"DATA-{counter:04d}"
                            
                            entries.append({
                                'entry_id': entry_id,
                                'issue': issue_text,
                                'bot_solution': bot_solution,
                                'ticket_type': ticket_type,
                                'smart_category': smart_category,
                                'category': category,
                                'type': type_name,
                                'item': item_name,
                            })
    
    return entries


def populate_kb():
    """Populate knowledge base from data.json file"""
    
    print("=" * 60)
    print("POPULATE KNOWLEDGE BASE SCRIPT (data.json)")
    print("=" * 60)
    
    # Path to data.json
    kb_json_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'kb', 'data', 'data.json'
    )
    
    print(f"\n📄 KB JSON Path: {kb_json_path}")
    
    # Check if file exists
    if not os.path.exists(kb_json_path):
        print(f"❌ KB file not found: {kb_json_path}")
        return False
    
    try:
        # Load JSON
        print("\n📖 Loading KB data from data.json...")
        with open(kb_json_path, 'r', encoding='utf-8') as f:
            kb_data = json.load(f)
        
        # Flatten the hierarchical structure into individual entries
        entries = flatten_data_json(kb_data)
        print(f"   Found {len(entries)} total issue entries")
        
        if not entries:
            print("❌ No entries found in data.json")
            return False
        
        # Count by ticket type
        type_counts = {}
        for e in entries:
            tt = e['ticket_type']
            type_counts[tt] = type_counts.get(tt, 0) + 1
        for tt, count in type_counts.items():
            print(f"   - {tt}: {count} entries")
        
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
        
        # Build unique categories from data.json hierarchy and insert into PostgreSQL
        print("\n📝 Inserting categories into PostgreSQL...")
        seen_categories = set()
        cat_counter = 0
        
        for entry in entries:
            # Use smart_category as the category key (top-level grouping under ticket_type)
            cat_key = entry['smart_category']
            if cat_key not in seen_categories:
                seen_categories.add(cat_key)
                cat_counter += 1
                cat_id = f"CAT-{cat_counter:03d}"
                try:
                    db.execute_query("""
                        INSERT INTO kb_categories (id, name, display_name, icon, display_order)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            name = EXCLUDED.name,
                            display_name = EXCLUDED.display_name,
                            icon = EXCLUDED.icon
                    """, (
                        cat_id,
                        cat_key,
                        cat_key,
                        '📋',
                        cat_counter
                    ))
                    print(f"   ✓ Category: {cat_key}")
                except Exception as e:
                    print(f"   ⚠ Error with category {cat_key}: {e}")
        
        # Initialize KB (ChromaDB)
        print("\n🔄 Initializing ChromaDB...")
        kb = KnowledgeBase()
        
        # Delete ALL existing ChromaDB entries first
        print("🗑️  Clearing existing ChromaDB entries...")
        kb.delete_all_entries()
        print("   ✓ Cleared ChromaDB")
        
        # Insert articles
        print("\n📝 Inserting articles into ChromaDB and PostgreSQL...")
        chromadb_count = 0
        postgres_count = 0
        
        for entry in entries:
            entry_id = entry['entry_id']
            issue = entry['issue']
            bot_solution = entry['bot_solution']
            
            # Build a rich search document combining issue + hierarchy path for better embedding
            search_text = f"{entry['item']} - {issue}"
            
            # Build keywords from hierarchy
            keywords = [
                entry['ticket_type'].lower(),
                entry['smart_category'].lower(),
                entry['category'].lower(),
                entry['type'].lower(),
                entry['item'].lower()
            ]
            
            # Insert into ChromaDB
            try:
                kb.add_entry(
                    issue=search_text,
                    solution=bot_solution,
                    source=f"{entry['ticket_type']} > {entry['smart_category']} > {entry['item']}",
                    entry_id=entry_id,
                    category=entry['smart_category'],
                    subcategory=entry['item'],
                    keywords=keywords
                )
                chromadb_count += 1
                if chromadb_count % 50 == 0:
                    print(f"   ... {chromadb_count} entries embedded")
            except Exception as e:
                print(f"   ⚠ ChromaDB error for {entry_id}: {e}")
            
            # Insert into PostgreSQL
            try:
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
                    entry_id,
                    issue,
                    entry['smart_category'],
                    entry['item'],
                    bot_solution,
                    keywords,
                    f"{entry['ticket_type']} > {entry['smart_category']} > {entry['item']}",
                    'System'
                ))
                postgres_count += 1
            except Exception as e:
                print(f"   ⚠ PostgreSQL error for {entry_id}: {e}")
        
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
        
        # Test a sample search
        print("\n🔍 Testing sample search...")
        test_results = kb.search("VPN connection issue", top_k=3)
        if test_results:
            for r in test_results[:3]:
                print(f"   - [{r['confidence']:.0%}] {r['issue'][:80]}")
        else:
            print("   ⚠ No search results returned")
        
        print("\n" + "=" * 60)
        print("✅ KNOWLEDGE BASE POPULATED SUCCESSFULLY FROM data.json!")
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
