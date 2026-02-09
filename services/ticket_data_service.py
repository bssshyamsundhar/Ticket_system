"""
Ticket Data Service - Handles navigation through the hierarchical ticket data structure
Supports the flow: Incident/Request → Smart Category → Category → Type → Item → Issue
"""
import json
import os
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class TicketDataService:
    """Service for navigating the ticket data hierarchy"""
    
    # Type declarations for instance attributes
    data_path: str
    _data_cache: Dict[str, Any]
    
    def __init__(self):
        # Try multiple possible locations for data.json
        possible_paths = [
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data.json'),
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'kb', 'data', 'data.json')
        ]
        
        self.data_path = possible_paths[1]  # Default to kb/data/data.json
        for path in possible_paths:
            if os.path.exists(path):
                self.data_path = path
                break
        
        self._data_cache = {"Incident": {}, "Request": {}}
        self._load_data()
    
    def _load_data(self):
        """Load data from JSON file"""
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                self._data_cache = json.load(f)
            logger.info(f"Loaded ticket data from {self.data_path}")
        except Exception as e:
            logger.error(f"Failed to load ticket data: {e}")
            self._data_cache = {"Incident": {}, "Request": {}}
    
    def reload_data(self):
        """Force reload data from file"""
        self._load_data()
    
    def get_ticket_types(self) -> List[Dict]:
        """
        Get top-level ticket types (Incident, Request)
        Returns list of buttons for the initial selection
        """
        return [
            {
                "id": "incident",
                "label": "🔧 Report an Issue (Incident)",
                "action": "select_ticket_type",
                "value": "Incident",
                "description": "Report problems or issues that need resolution"
            },
            {
                "id": "request",
                "label": "📝 Make a Request",
                "action": "select_ticket_type",
                "value": "Request",
                "description": "Request new equipment, access, or services"
            }
        ]
    
    def get_smart_categories(self, ticket_type: str = "Incident") -> List[Dict]:
        """
        Get smart categories for a ticket type
        e.g., "Network Connection Issues", "Operating System Issues", etc.
        """
        try:
            type_data = self._data_cache.get(ticket_type, {})
            
            if not type_data:
                return []
            
            # Define icons for smart categories
            icons = {
                "Network Connection Issues": "🌐",
                "Operating System Issues": "💻",
                "PC / Laptop / Peripherals / Accessories Issues": "🖥️",
                "Printer / Scanner / Copier Issues": "🖨️",
                "Laptop Request": "💻",
                "Modification Request": "🔧",
                "Access Request": "🔑"
            }
            
            categories = []
            for idx, smart_cat in enumerate(type_data.keys()):
                categories.append({
                    "id": f"smart_cat_{idx}",
                    "label": f"{icons.get(smart_cat, '📁')} {smart_cat}",
                    "action": "select_smart_category",
                    "value": smart_cat,
                    "icon": icons.get(smart_cat, "📁")
                })
            
            return categories
        except Exception as e:
            logger.error(f"Error getting smart categories: {e}")
            return []
    
    def get_categories(self, ticket_type: str, smart_category: str) -> List[Dict]:
        """
        Get categories within a smart category
        e.g., "Hardware & Connectivity", "Applications & Software"
        """
        try:
            smart_cat_data = self._data_cache.get(ticket_type, {}).get(smart_category, {})
            
            if not smart_cat_data:
                return []
            
            icons = {
                "Hardware & Connectivity": "🔌",
                "Applications & Software": "📱"
            }
            
            categories = []
            for idx, category in enumerate(smart_cat_data.keys()):
                categories.append({
                    "id": f"cat_{idx}",
                    "label": f"{icons.get(category, '📂')} {category}",
                    "action": "select_category",
                    "value": category,
                    "icon": icons.get(category, "📂")
                })
            
            return categories
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return []
    
    def get_types(self, ticket_type: str, smart_category: str, category: str) -> List[Dict]:
        """
        Get types within a category
        e.g., "Network", "Windows 10", "Laptop", etc.
        """
        try:
            category_data = self._data_cache.get(ticket_type, {}).get(smart_category, {}).get(category, {})
            
            if not category_data:
                return []
            
            # Define icons for common types
            type_icons = {
                "Network": "🌐",
                "Windows 10": "🪟",
                "Windows 11": "🪟",
                "Biometric": "👆",
                "Laptop/ Desktop": "💻",
                "Datacard": "📶",
                "Desktop": "🖥️",
                "Headset": "🎧",
                "Laptop": "💻",
                "Monitor": "🖥️",
                "Printer/Scanner/Copier": "🖨️"
            }
            
            types = []
            for idx, type_name in enumerate(category_data.keys()):
                types.append({
                    "id": f"type_{idx}",
                    "label": f"{type_icons.get(type_name, '📋')} {type_name}",
                    "action": "select_type",
                    "value": type_name,
                    "icon": type_icons.get(type_name, "📋")
                })
            
            return types
        except Exception as e:
            logger.error(f"Error getting types: {e}")
            return []
    
    def get_items(self, ticket_type: str, smart_category: str, category: str, type_name: str) -> List[Dict]:
        """
        Get items within a type
        e.g., "Network Port", "Zoom Phone", "Battery Problems", etc.
        """
        try:
            type_data = self._data_cache.get(ticket_type, {}).get(smart_category, {}).get(category, {}).get(type_name, {})
            
            if not type_data:
                return []
            
            items = []
            for idx, item_name in enumerate(type_data.keys()):
                # Count issues in this item
                issues = type_data.get(item_name, [])
                issue_count = len(issues) if isinstance(issues, list) else 0
                
                items.append({
                    "id": f"item_{idx}",
                    "label": f"📌 {item_name}",
                    "action": "select_item",
                    "value": item_name,
                    "issue_count": issue_count
                })
            
            return items
        except Exception as e:
            logger.error(f"Error getting items: {e}")
            return []
    
    def get_issues(self, ticket_type: str, smart_category: str, category: str, 
                   type_name: str, item_name: str) -> List[Dict]:
        """
        Get issues within an item
        Returns the list of specific issues with their solutions
        """
        try:
            issues_data = self._data_cache.get(ticket_type, {}).get(smart_category, {}).get(category, {}).get(type_name, {}).get(item_name, [])
            
            if not issues_data or not isinstance(issues_data, list):
                return []
            
            issues = []
            for idx, issue in enumerate(issues_data):
                issues.append({
                    "id": f"issue_{idx}",
                    "label": f"❓ {issue.get('issue', 'Unknown Issue')}",
                    "action": "select_issue",
                    "value": str(idx),  # Use index as value
                    "issue_text": issue.get('issue', ''),
                    "bot_solution": issue.get('bot_solution', '')
                })
            
            # Add "Other Issue" option at the end
            issues.append({
                "id": "other_issue",
                "label": "❓ Other Issue (Not Listed)",
                "action": "other_issue",
                "value": "other",
                "is_other": True
            })
            
            return issues
        except Exception as e:
            logger.error(f"Error getting issues: {e}")
            return []
    
    def get_issue_solution(self, ticket_type: str, smart_category: str, category: str,
                           type_name: str, item_name: str, issue_index: int) -> Optional[Dict]:
        """
        Get a specific issue and its solution by index
        """
        try:
            issues_data = self._data_cache.get(ticket_type, {}).get(smart_category, {}).get(category, {}).get(type_name, {}).get(item_name, [])
            
            if not issues_data or not isinstance(issues_data, list):
                return None
            
            if 0 <= issue_index < len(issues_data):
                issue = issues_data[issue_index]
                return {
                    "issue": issue.get('issue', ''),
                    "bot_solution": issue.get('bot_solution', ''),
                    "smart_category": smart_category,
                    "category": category,
                    "type": type_name,
                    "item": item_name
                }
            
            return None
        except Exception as e:
            logger.error(f"Error getting issue solution: {e}")
            return None
    
    def search_issues(self, query: str, ticket_type: str = "Incident") -> List[Dict]:
        """
        Search for issues across all categories (for "Other Issue" free text)
        Returns top matching issues based on keyword matching
        """
        try:
            results = []
            query_lower = query.lower()
            query_words = set(query_lower.split())
            
            type_data = self._data_cache.get(ticket_type, {})
            
            for smart_cat, categories in type_data.items():
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
                            for idx, issue in enumerate(issues):
                                issue_text = issue.get('issue', '').lower()
                                solution_text = issue.get('bot_solution', '').lower()
                                
                                # Calculate relevance score
                                score = 0
                                for word in query_words:
                                    if word in issue_text:
                                        score += 3  # Higher weight for issue text
                                    if word in solution_text:
                                        score += 1
                                
                                if score > 0:
                                    results.append({
                                        "score": score,
                                        "issue": issue.get('issue', ''),
                                        "bot_solution": issue.get('bot_solution', ''),
                                        "smart_category": smart_cat,
                                        "category": category,
                                        "type": type_name,
                                        "item": item_name,
                                        "issue_index": idx
                                    })
            
            # Sort by score descending and return top 5
            results.sort(key=lambda x: x['score'], reverse=True)
            return results[:5]  # type: ignore[index]
        except Exception as e:
            logger.error(f"Error searching issues: {e}")
            return []
    
    def validate_path(self, ticket_type: str, smart_category: Optional[str] = None, 
                      category: Optional[str] = None, type_name: Optional[str] = None, 
                      item_name: Optional[str] = None) -> bool:
        """
        Validate that a navigation path exists in the data
        """
        try:
            data = self._data_cache.get(ticket_type)
            if data is None:
                return False
            
            if smart_category:
                data = data.get(smart_category)
                if data is None:
                    return False
            
            if category:
                data = data.get(category)
                if data is None:
                    return False
            
            if type_name:
                data = data.get(type_name)
                if data is None:
                    return False
            
            if item_name:
                data = data.get(item_name)
                if data is None:
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Error validating path: {e}")
            return False


# Global instance
ticket_data_service = TicketDataService()
