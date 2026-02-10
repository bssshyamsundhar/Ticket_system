"""
Request Flow Handler - Handles IT Hardware, Software, and Access request flows
Integrates with main chat_handler for request ticket creation with manager approval
"""
import random

# Hardware brand options for each item
HARDWARE_BRANDS = {
    'Laptop': [
        {'id': 'hp_laptop', 'label': '💻 HP', 'value': 'HP Laptop'},
        {'id': 'dell_laptop', 'label': '💻 Dell', 'value': 'Dell Laptop'},
        {'id': 'lenovo_laptop', 'label': '💻 Lenovo', 'value': 'Lenovo Laptop'},
        {'id': 'macbook', 'label': '🍎 MacBook', 'value': 'Apple MacBook'},
        {'id': 'other_laptop', 'label': '📝 Other', 'value': 'Other Laptop'},
    ],
    'Desktop': [
        {'id': 'hp_desktop', 'label': '🖥️ HP', 'value': 'HP Desktop'},
        {'id': 'dell_desktop', 'label': '🖥️ Dell', 'value': 'Dell Desktop'},
        {'id': 'lenovo_desktop', 'label': '🖥️ Lenovo', 'value': 'Lenovo Desktop'},
        {'id': 'other_desktop', 'label': '📝 Other', 'value': 'Other Desktop'},
    ],
    'Monitor': [
        {'id': 'dell_monitor', 'label': '🖵 Dell', 'value': 'Dell Monitor'},
        {'id': 'hp_monitor', 'label': '🖵 HP', 'value': 'HP Monitor'},
        {'id': 'lg_monitor', 'label': '🖵 LG', 'value': 'LG Monitor'},
        {'id': 'samsung_monitor', 'label': '🖵 Samsung', 'value': 'Samsung Monitor'},
        {'id': 'other_monitor', 'label': '📝 Other', 'value': 'Other Monitor'},
    ],
    'Keyboard': [
        {'id': 'standard_kb', 'label': '⌨️ Standard Keyboard', 'value': 'Standard Keyboard'},
        {'id': 'ergonomic_kb', 'label': '⌨️ Ergonomic Keyboard', 'value': 'Ergonomic Keyboard'},
        {'id': 'wireless_kb', 'label': '⌨️ Wireless Keyboard', 'value': 'Wireless Keyboard'},
        {'id': 'other_kb', 'label': '📝 Other', 'value': 'Other Keyboard'},
    ],
    'Mouse': [
        {'id': 'standard_mouse', 'label': '🖱️ Standard Mouse', 'value': 'Standard Mouse'},
        {'id': 'ergonomic_mouse', 'label': '🖱️ Ergonomic Mouse', 'value': 'Ergonomic Mouse'},
        {'id': 'wireless_mouse', 'label': '🖱️ Wireless Mouse', 'value': 'Wireless Mouse'},
        {'id': 'other_mouse', 'label': '📝 Other', 'value': 'Other Mouse'},
    ],
    'Headset': [
        {'id': 'jabra', 'label': '🎧 Jabra', 'value': 'Jabra Headset'},
        {'id': 'plantronics', 'label': '🎧 Plantronics', 'value': 'Plantronics Headset'},
        {'id': 'logitech_hs', 'label': '🎧 Logitech', 'value': 'Logitech Headset'},
        {'id': 'other_headset', 'label': '📝 Other', 'value': 'Other Headset'},
    ],
    'Webcam': [
        {'id': 'logitech_cam', 'label': '📷 Logitech', 'value': 'Logitech Webcam'},
        {'id': 'hp_cam', 'label': '📷 HP', 'value': 'HP Webcam'},
        {'id': 'dell_cam', 'label': '📷 Dell', 'value': 'Dell Webcam'},
        {'id': 'other_webcam', 'label': '📝 Other', 'value': 'Other Webcam'},
    ],
    'Docking Station': [
        {'id': 'hp_dock', 'label': '🔌 HP', 'value': 'HP Docking Station'},
        {'id': 'dell_dock', 'label': '🔌 Dell', 'value': 'Dell Docking Station'},
        {'id': 'lenovo_dock', 'label': '🔌 Lenovo', 'value': 'Lenovo Docking Station'},
        {'id': 'other_dock', 'label': '📝 Other', 'value': 'Other Docking Station'},
    ],
}

# Request categories and options
REQUEST_CATEGORIES = {
    'hardware': {
        'id': 'hardware',
        'label': '🖥️ IT Hardware Request',
        'action': 'select_request_category',
        'value': 'hardware',
        'items': [
            {'id': 'laptop', 'label': '💻 Laptop', 'value': 'Laptop'},
            {'id': 'desktop', 'label': '🖥️ Desktop', 'value': 'Desktop'},
            {'id': 'monitor', 'label': '🖵 Monitor', 'value': 'Monitor'},
            {'id': 'keyboard', 'label': '⌨️ Keyboard', 'value': 'Keyboard'},
            {'id': 'mouse', 'label': '🖱️ Mouse', 'value': 'Mouse'},
            {'id': 'headset', 'label': '🎧 Headset', 'value': 'Headset'},
            {'id': 'webcam', 'label': '📷 Webcam', 'value': 'Webcam'},
            {'id': 'docking_station', 'label': '🔌 Docking Station', 'value': 'Docking Station'},
            {'id': 'other_hardware', 'label': '📝 Other Hardware', 'value': 'Other Hardware'},
        ]
    },
    'software': {
        'id': 'software',
        'label': '💿 Install/Remove Software',
        'action': 'select_request_category',
        'value': 'software',
        'actions': [
            {'id': 'install', 'label': '📥 Install Software', 'action': 'select_software_action', 'value': 'install'},
            {'id': 'remove', 'label': '📤 Remove Software', 'action': 'select_software_action', 'value': 'remove'}
        ],
        'items': [
            {'id': 'adobe_acrobat', 'label': 'Adobe Acrobat Pro', 'value': 'Adobe Acrobat Pro'},
            {'id': 'ms_visio', 'label': 'Microsoft Visio', 'value': 'Microsoft Visio'},
            {'id': 'ms_project', 'label': 'Microsoft Project', 'value': 'Microsoft Project'},
            {'id': 'autocad', 'label': 'AutoCAD', 'value': 'AutoCAD'},
            {'id': 'zoom', 'label': 'Zoom', 'value': 'Zoom'},
            {'id': 'slack', 'label': 'Slack', 'value': 'Slack'},
            {'id': 'other', 'label': '📝 Other Software', 'value': 'Other'}
        ]
    },
    'access': {
        'id': 'access',
        'label': '🔐 Access Related',
        'action': 'select_request_category',
        'value': 'access',
        'types': [
            {'id': 'internet', 'label': '🌐 Internet Access', 'action': 'select_access_type', 'value': 'internet'},
            {'id': 'shared_folder', 'label': '📁 Shared Folder Access', 'action': 'select_access_type', 'value': 'shared_folder'},
            {'id': 'vpn', 'label': '🔒 VPN Access', 'action': 'select_access_type', 'value': 'vpn'}
        ],
        'internet_options': [
            {'id': 'ai_internet', 'label': 'AI Internet Access', 'value': 'AI Internet Access'},
            {'id': 'hr_access', 'label': 'HR Portal Access', 'value': 'HR Portal Access'},
            {'id': 'social_media', 'label': 'Social Media Access', 'value': 'Social Media Access'},
            {'id': 'dev_tools', 'label': 'Developer Tools Access', 'value': 'Developer Tools Access'},
            {'id': 'cloud_storage', 'label': 'Cloud Storage Access', 'value': 'Cloud Storage Access'}
        ],
        'folder_permissions': [
            {'id': 'read', 'label': '👁️ Read Only', 'action': 'select_folder_permission', 'value': 'Read'},
            {'id': 'write', 'label': '✏️ Write Only', 'action': 'select_folder_permission', 'value': 'Write'},
            {'id': 'rw', 'label': '📝 Read & Write', 'action': 'select_folder_permission', 'value': 'Read/Write'}
        ]
    }
}

# Request flow states
STATE_REQUEST_CATEGORY = 'request_category'
STATE_REQUEST_HARDWARE_TYPE = 'request_hardware_type'
STATE_REQUEST_HARDWARE_BRAND = 'request_hardware_brand'
STATE_REQUEST_SOFTWARE_ACTION = 'request_software_action'
STATE_REQUEST_SOFTWARE_TYPE = 'request_software_type'
STATE_REQUEST_ACCESS_TYPE = 'request_access_type'
STATE_REQUEST_INTERNET_ACCESS = 'request_internet_access'
STATE_REQUEST_SHARED_FOLDER_PATH = 'request_shared_folder_path'
STATE_REQUEST_SHARED_FOLDER_PERMISSION = 'request_shared_folder_permission'
STATE_REQUEST_VPN_REASON = 'request_vpn_reason'
STATE_REQUEST_JUSTIFICATION = 'request_justification'
STATE_REQUEST_PREVIEW = 'request_preview'
STATE_MANAGER_APPROVAL = 'manager_approval'


def get_request_categories():
    """Get main request category buttons"""
    return [
        {'id': 'hardware', 'label': '🖥️ IT Hardware Request', 'action': 'select_request_category', 'value': 'hardware'},
        {'id': 'software', 'label': '💿 Install/Remove Software', 'action': 'select_request_category', 'value': 'software'},
        {'id': 'access', 'label': '🔐 Access Related', 'action': 'select_request_category', 'value': 'access'}
    ]


def handle_request_category(value, conversation_state):
    """Handle request category selection"""
    conversation_state['request_category'] = value
    conversation_state['state'] = STATE_REQUEST_CATEGORY
    conversation_state.setdefault('navigation_stack', []).append(('request_category', value))
    
    if value == 'hardware':
        conversation_state['state'] = STATE_REQUEST_HARDWARE_TYPE
        buttons = [{'id': item['id'], 'label': item['label'], 
                   'action': 'select_hardware_item', 'value': item['value']} 
                   for item in REQUEST_CATEGORIES['hardware']['items']]
        buttons.append({'id': 'back', 'label': '⬅️ Go Back', 'action': 'go_back', 'value': 'back'})
        
        return {
            "success": True,
            "response": "🖥️ **IT Hardware Request**\n\nPlease select the hardware you need:",
            "buttons": buttons,
            "state": STATE_REQUEST_HARDWARE_TYPE,
            "show_text_input": False
        }
    
    elif value == 'software':
        conversation_state['state'] = STATE_REQUEST_SOFTWARE_ACTION
        buttons = REQUEST_CATEGORIES['software']['actions'] + [
            {'id': 'back', 'label': '⬅️ Go Back', 'action': 'go_back', 'value': 'back'}
        ]
        
        return {
            "success": True,
            "response": "💿 **Software Request**\n\nWould you like to install or remove software?",
            "buttons": buttons,
            "state": STATE_REQUEST_SOFTWARE_ACTION,
            "show_text_input": False
        }
    
    elif value == 'access':
        conversation_state['state'] = STATE_REQUEST_ACCESS_TYPE
        buttons = REQUEST_CATEGORIES['access']['types'] + [
            {'id': 'back', 'label': '⬅️ Go Back', 'action': 'go_back', 'value': 'back'}
        ]
        
        return {
            "success": True,
            "response": "🔐 **Access Request**\n\nPlease select the type of access you need:",
            "buttons": buttons,
            "state": STATE_REQUEST_ACCESS_TYPE,
            "show_text_input": False
        }
    
    return None


def handle_hardware_item(value, conversation_state):
    """Handle hardware item selection - show brand options"""
    conversation_state['request_item'] = value
    conversation_state['state'] = STATE_REQUEST_HARDWARE_BRAND
    conversation_state.setdefault('navigation_stack', []).append(('request_hardware_type', value))
    
    # "Other Hardware" - prompt for free text description
    if value == 'Other Hardware':
        conversation_state['state'] = STATE_REQUEST_HARDWARE_BRAND
        return {
            "success": True,
            "response": "📝 **Other Hardware Request**\n\nPlease describe the hardware you need:",
            "buttons": [{'id': 'back', 'label': '⬅️ Go Back', 'action': 'go_back', 'value': 'back'}],
            "state": STATE_REQUEST_HARDWARE_BRAND,
            "show_text_input": True
        }
    
    brands = HARDWARE_BRANDS.get(value, [])
    if not brands:
        # Fallback: go directly to preview
        conversation_state['state'] = STATE_REQUEST_PREVIEW
        return build_request_preview(conversation_state)
    
    buttons = [{'id': b['id'], 'label': b['label'], 
               'action': 'select_hardware_brand', 'value': b['value']} 
               for b in brands]
    buttons.append({'id': 'back', 'label': '⬅️ Go Back', 'action': 'go_back', 'value': 'back'})
    
    return {
        "success": True,
        "response": f"💻 **{value} Request**\n\nPlease select the brand/type:",
        "buttons": buttons,
        "state": STATE_REQUEST_HARDWARE_BRAND,
        "show_text_input": False
    }


def handle_hardware_brand(value, conversation_state):
    """Handle hardware brand selection - go directly to preview or show text input for Other"""
    # If user selected "Other" brand, prompt for specification
    if value.startswith('Other '):
        conversation_state['hardware_other_type'] = value.replace('Other ', '')
        conversation_state['state'] = STATE_REQUEST_HARDWARE_BRAND
        return {
            "success": True,
            "response": f"📝 **Other {value.replace('Other ', '')}**\n\nPlease specify the brand/model you need:",
            "buttons": [{'id': 'back', 'label': '⬅️ Go Back', 'action': 'go_back', 'value': 'back'}],
            "state": STATE_REQUEST_HARDWARE_BRAND,
            "show_text_input": True
        }
    
    conversation_state['request_item'] = value  # e.g. "HP Laptop"
    conversation_state['justification'] = f"Requesting {value}"
    conversation_state['state'] = STATE_REQUEST_PREVIEW
    conversation_state.setdefault('navigation_stack', []).append(('request_hardware_brand', value))
    
    return build_request_preview(conversation_state)


def handle_software_action(value, conversation_state):
    """Handle software install/remove action selection"""
    conversation_state['software_action'] = value
    conversation_state['state'] = STATE_REQUEST_SOFTWARE_TYPE
    conversation_state.setdefault('navigation_stack', []).append(('request_software_action', value))
    
    action_text = "install" if value == "install" else "remove"
    buttons = [{'id': item['id'], 'label': item['label'], 
               'action': 'select_software_item', 'value': item['value']} 
               for item in REQUEST_CATEGORIES['software']['items']]
    buttons.append({'id': 'back', 'label': '⬅️ Go Back', 'action': 'go_back', 'value': 'back'})
    
    return {
        "success": True,
        "response": f"💿 **Software {action_text.title()}**\n\nPlease select the software to {action_text}:",
        "buttons": buttons,
        "state": STATE_REQUEST_SOFTWARE_TYPE,
        "show_text_input": False
    }


def handle_software_item(value, conversation_state):
    """Handle software item selection - go directly to preview"""
    conversation_state['request_item'] = value
    conversation_state.setdefault('navigation_stack', []).append(('request_software_type', value))
    
    if value == 'Other':
        conversation_state['state'] = STATE_REQUEST_SOFTWARE_TYPE
        return {
            "success": True,
            "response": "📝 **Other Software**\n\nPlease enter the software name:",
            "buttons": [{'id': 'back', 'label': '⬅️ Go Back', 'action': 'go_back', 'value': 'back'}],
            "state": STATE_REQUEST_SOFTWARE_TYPE,
            "show_text_input": True
        }
    
    action = conversation_state.get('software_action', 'install')
    conversation_state['justification'] = f"Requesting {action} of {value}"
    conversation_state['state'] = STATE_REQUEST_PREVIEW
    
    return build_request_preview(conversation_state)


def handle_access_type(value, conversation_state):
    """Handle access type selection"""
    conversation_state['access_type'] = value
    conversation_state.setdefault('navigation_stack', []).append(('request_access_type', value))
    
    if value == 'internet':
        conversation_state['state'] = STATE_REQUEST_INTERNET_ACCESS
        options = REQUEST_CATEGORIES['access']['internet_options']
        
        return {
            "success": True,
            "response": "🌐 **Internet Access Request**\n\nSelect the access types you need (you can select multiple):",
            "checkboxes": options,  # Frontend will render as checkboxes
            "buttons": [
                {'id': 'confirm', 'label': '✅ Confirm Selection', 'action': 'confirm_internet_access', 'value': 'confirm'},
                {'id': 'back', 'label': '⬅️ Go Back', 'action': 'go_back', 'value': 'back'}
            ],
            "state": STATE_REQUEST_INTERNET_ACCESS,
            "show_text_input": False,
            "show_checkboxes": True
        }
    
    elif value == 'shared_folder':
        conversation_state['state'] = STATE_REQUEST_SHARED_FOLDER_PATH
        conversation_state.setdefault('navigation_stack', []).append(('request_access_folder', value))
        
        return {
            "success": True,
            "response": "📁 **Shared Folder Access**\n\nPlease enter the folder path (e.g., \\\\server\\share\\folder):",
            "buttons": [{'id': 'back', 'label': '⬅️ Go Back', 'action': 'go_back', 'value': 'back'}],
            "state": STATE_REQUEST_SHARED_FOLDER_PATH,
            "show_text_input": True
        }
    
    elif value == 'vpn':
        # Skip reason prompt, go directly to preview with VPN access
        conversation_state['request_item'] = 'VPN Access'
        conversation_state['justification'] = 'VPN access required for remote work'
        conversation_state['state'] = STATE_REQUEST_PREVIEW
        conversation_state.setdefault('navigation_stack', []).append(('request_access_vpn', 'vpn'))
        
        return build_request_preview(conversation_state)
    
    return None


def handle_internet_access_confirm(selected_options, conversation_state):
    """Handle internet access checkbox selection confirmation - go directly to preview"""
    conversation_state['internet_access_types'] = selected_options
    conversation_state['request_item'] = ', '.join(selected_options) if selected_options else 'Internet Access'
    conversation_state['justification'] = f"Requesting access to: {conversation_state['request_item']}"
    conversation_state['state'] = STATE_REQUEST_PREVIEW
    conversation_state.setdefault('navigation_stack', []).append(('request_internet_confirm', 'confirm'))
    
    return build_request_preview(conversation_state)


def handle_shared_folder_path(folder_path, conversation_state):
    """Handle shared folder path input"""
    conversation_state['folder_path'] = folder_path
    conversation_state['state'] = STATE_REQUEST_SHARED_FOLDER_PERMISSION
    conversation_state.setdefault('navigation_stack', []).append(('request_folder_path', folder_path))
    
    buttons = REQUEST_CATEGORIES['access']['folder_permissions'] + [
        {'id': 'back', 'label': '⬅️ Go Back', 'action': 'go_back', 'value': 'back'}
    ]
    
    return {
        "success": True,
        "response": f"📁 **Folder: {folder_path}**\n\nSelect the permission level you need:",
        "buttons": buttons,
        "state": STATE_REQUEST_SHARED_FOLDER_PERMISSION,
        "show_text_input": False
    }


def handle_folder_permission(value, conversation_state):
    """Handle folder permission selection - go directly to preview"""
    conversation_state['folder_permission'] = value
    folder_path = conversation_state.get('folder_path', 'Unknown')
    conversation_state['request_item'] = f"Shared Folder: {folder_path} ({value})"
    conversation_state['justification'] = f"Requesting {value} access to {folder_path}"
    conversation_state['state'] = STATE_REQUEST_PREVIEW
    conversation_state.setdefault('navigation_stack', []).append(('request_folder_permission', value))
    
    return build_request_preview(conversation_state)


def handle_vpn_reason(reason, conversation_state):
    """Handle VPN reason input"""
    conversation_state['vpn_reason'] = reason
    conversation_state['request_item'] = 'VPN Access'
    conversation_state['justification'] = reason
    conversation_state['state'] = STATE_REQUEST_PREVIEW
    
    return build_request_preview(conversation_state)


def handle_justification(justification, conversation_state):
    """Handle justification input"""
    conversation_state['justification'] = justification
    conversation_state['state'] = STATE_REQUEST_PREVIEW
    
    return build_request_preview(conversation_state)


def build_request_preview(conversation_state):
    """Build request preview for confirmation"""
    category = conversation_state.get('request_category', 'General')
    item = conversation_state.get('request_item', 'Unknown')
    justification = conversation_state.get('justification', 'No justification provided')
    software_action = conversation_state.get('software_action', '')
    
    # Build request details
    if category == 'hardware':
        request_type = f"🖥️ Hardware Request: {item}"
    elif category == 'software':
        action = 'Installation' if software_action == 'install' else 'Removal'
        request_type = f"💿 Software {action}: {item}"
    elif category == 'access':
        access_type = conversation_state.get('access_type', '')
        if access_type == 'internet':
            request_type = f"🌐 Internet Access: {item}"
        elif access_type == 'shared_folder':
            request_type = f"📁 Shared Folder Access: {item}"
        elif access_type == 'vpn':
            request_type = f"🔒 VPN Access"
        else:
            request_type = f"🔐 Access Request: {item}"
    else:
        request_type = f"📋 Request: {item}"
    
    preview = f"""📋 **Request Preview**

**Type:** {request_type}

**Justification:** {justification}

---
Would you like to submit this request?"""
    
    return {
        "success": True,
        "response": preview,
        "buttons": [
            {'id': 'confirm', 'label': '✅ Submit Request', 'action': 'submit_request', 'value': 'yes'},
            {'id': 'cancel', 'label': '❌ Cancel', 'action': 'start', 'value': 'no'}
        ],
        "state": STATE_REQUEST_PREVIEW,
        "show_text_input": False
    }


def handle_submit_request(conversation_state, user_info):
    """Handle request submission - show waiting for manager approval (no ticket created)"""
    item = conversation_state.get('request_item', 'Unknown')
    
    # Generate simulated manager name
    manager_names = ["Maheshwar"]
    simulated_manager = random.choice(manager_names)
    conversation_state['simulated_manager'] = simulated_manager
    conversation_state['state'] = 'request_complete'
    
    return {
        "success": True,
        "response": f"✅ **Request Submitted Successfully!**\n\nYour request for **{item}** has been forwarded to **Manager {simulated_manager}** for approval.\n\n📧 We'll notify you via email once the manager approves your request.\n\n---\n\nWould you like to do anything else?",
        "buttons": [
            {'id': 'new', 'label': '🆕 New Request', 'action': 'start', 'value': 'new'},
            {'id': 'done', 'label': '✅ I\'m Done', 'action': 'end', 'value': 'done'}
        ],
        "state": 'request_complete',
        "show_text_input": False
    }


def handle_check_approval(conversation_state):
    """Simulate manager approval check - always approves"""
    simulated_manager = conversation_state.get('simulated_manager', 'Your Manager')
    item = conversation_state.get('request_item', 'Unknown')
    conversation_state['state'] = 'manager_approved'
    
    return {
        "success": True,
        "response": f"✅ **Request Approved!**\n\n👤 **Manager {simulated_manager}** has reviewed and approved your request for **{item}**.\n\n📧 You will receive a confirmation email shortly.\n\n---\n\nWould you like to do anything else?",
        "buttons": [
            {'id': 'new', 'label': '🆕 New Request', 'action': 'start', 'value': 'new'},
            {'id': 'done', 'label': '✅ I\'m Done', 'action': 'end', 'value': 'done'}
        ],
        "state": 'manager_approved',
        "show_text_input": False
    }


def get_manager_approval_message(manager_name=None, ticket_id=None):
    """Get the manager approval confirmation message with simulated approval"""
    manager_name = manager_name or "Your Manager"
    ticket_msg = f" (Ticket: **{ticket_id}**)" if ticket_id else ""
    
    return {
        "success": True,
        "response": f"✅ **Request Approved!**{ticket_msg}\n\n👤 **Manager {manager_name}** has reviewed and approved your request.\n\n📧 You will receive a confirmation email shortly.\n\n---\n\nWould you like to do anything else?",
        "buttons": [
            {'id': 'new', 'label': '🆕 New Request', 'action': 'start', 'value': 'new'},
            {'id': 'done', 'label': '✅ I\'m Done', 'action': 'end', 'value': 'done'}
        ],
        "state": STATE_MANAGER_APPROVAL,
        "show_text_input": False
    }
