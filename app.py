"""Flask REST API for IT Support System - Updated with Dashboard Integration and Button-Based Navigation"""

# Disable TensorFlow before any imports (must be at very top)
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TRANSFORMERS_NO_TF'] = '1'
os.environ['USE_TF'] = '0'

from flask import Flask, request, jsonify, g
from flask_cors import CORS
import asyncio
import logging
import jwt
import bcrypt
from datetime import datetime, timedelta, timezone
from functools import wraps
from config import config
from db.postgres import db
from kb.kb_chroma import kb
from runners.run_agents import orchestrator
from services.email_service import email_service
from services.cloudinary_service import cloudinary_service
from services.chat_handler import chat_handler  # New navigation handler
from services.ticket_data_service import ticket_data_service  # New data service
from services import feedback_handler
import time
import json
import base64

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure werkzeug request logs (GET/POST etc.) are visible
logging.getLogger('werkzeug').setLevel(logging.INFO)

# Create or get event loop for async operations
def get_or_create_event_loop():
    """Get existing event loop or create a new one"""
    try:
        return asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop

def run_async(coro):
    """Run an async coroutine from sync code"""
    loop = get_or_create_event_loop()
    return loop.run_until_complete(coro)

# Create Flask app
app = Flask(__name__)
CORS(app)

# Enable JSON minification in production
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

# Custom JSON encoder: naive datetime objects are treated as UTC and serialized with 'Z' suffix
# Flask's default uses http_date() which treats naive datetimes as UTC in RFC 2822 format,
# but our DB was storing IST times, causing a +5:30h offset on the frontend.
from flask.json.provider import DefaultJSONProvider
from datetime import date as date_type, time as time_type

class UTCJSONProvider(DefaultJSONProvider):
    """Ensures all datetime objects are serialized as UTC ISO 8601 strings with 'Z' suffix."""
    def default(self, o):
        # datetime must be checked before date (datetime is subclass of date)
        if isinstance(o, datetime):
            # If naive (no tzinfo), assume UTC (guaranteed by DB connection TimeZone=UTC)
            if o.tzinfo is None:
                return o.isoformat() + 'Z'
            # If aware, convert to UTC then format
            utc_dt = o.astimezone(timezone.utc)
            return utc_dt.strftime('%Y-%m-%dT%H:%M:%SZ')
        if isinstance(o, date_type):
            return o.isoformat()  # "2026-02-10"
        if isinstance(o, time_type):
            return o.isoformat()  # "09:00:00"
        return super().default(o)

app.json_provider_class = UTCJSONProvider
app.json = UTCJSONProvider(app)

# JWT Secret (from environment variables)
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_EXPIRATION_HOURS = 24

# Store conversation states (in production, use Redis or similar)
# Key format: "user_id_session_id" -> conversation_state dict
conversation_states = {}


# Performance monitoring middleware
@app.before_request
def before_request():
    """Track request start time for performance monitoring"""
    g.start_time = time.time()


@app.after_request
def after_request(response):
    """Log request processing time"""
    if hasattr(g, 'start_time'):
        elapsed = time.time() - g.start_time
        if elapsed > 1.0:  # Log slow requests (> 1 second)
            logger.warning(f"Slow request: {request.method} {request.path} took {elapsed:.2f}s")
    
    # Add security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    return response


def token_required(f):
    """Decorator to check JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Check for token in Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({"success": False, "error": "Invalid token format"}), 401
        
        if not token:
            return jsonify({"success": False, "error": "Token is missing"}), 401
        
        try:
            data = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            request.user_id = data['user_id']
            request.user_email = data['email']
            request.user_name = data.get('name', data.get('username', 'User'))
            request.user_role = data['role']
        except jwt.ExpiredSignatureError:
            return jsonify({"success": False, "error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"success": False, "error": "Invalid token"}), 401
        
        return f(*args, **kwargs)
    
    return decorated


def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if request.user_role != 'admin':
            return jsonify({"success": False, "error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "IT Support System",
        "version": "2.0.0"
    })


@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user"""
    try:
        data = request.json
        name = data.get('name') or data.get('username')  # Support both
        email = data.get('email')
        password = data.get('password')
        department = data.get('department')
        
        if not all([name, email, password]):
            return jsonify({
                "success": False,
                "error": "name, email, and password are required"
            }), 400
        
        # Check if user already exists
        if db.user_exists(email):
            return jsonify({
                "success": False,
                "error": "User with this email already exists"
            }), 409
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Create user
        user = db.create_user(name, email, password_hash, 'user', department)
        
        if user:
            # Generate JWT token
            token = jwt.encode({
                'user_id': user['id'],
                'email': email,
                'name': name,
                'role': 'user',
                'exp': datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
            }, JWT_SECRET, algorithm="HS256")
            
            return jsonify({
                "success": True,
                "token": token,
                "user": {
                    "id": user['id'],
                    "name": name,
                    "email": email,
                    "role": "user"
                }
            }), 201
        else:
            return jsonify({
                "success": False,
                "error": "Failed to create user"
            }), 500
    
    except Exception as e:
        logger.error(f"Error registering user: {type(e).__name__}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": f"{type(e).__name__}: {str(e)}"
        }), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login a user with email and password"""
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        
        if not email or not password:
            return jsonify({
                "success": False,
                "error": "email and password are required"
            }), 400
        
        # Get user by email
        user = db.get_user_by_email(email)
        
        if not user:
            return jsonify({
                "success": False,
                "error": "Invalid email or password"
            }), 401
        
        # Check password
        if not user.get('password_hash') or not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
            return jsonify({
                "success": False,
                "error": "Invalid email or password"
            }), 401
        
        # Generate JWT token
        token = jwt.encode({
            'user_id': user['id'],
            'email': user['email'],
            'name': user['name'],
            'role': user['role'],
            'exp': datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRATION_HOURS)
        }, JWT_SECRET, algorithm="HS256")
        
        return jsonify({
            "success": True,
            "token": token,
            "user": {
                "id": user['id'],
                "name": user['name'],
                "email": user['email'],
                "role": user['role']
            }
        })
    
    except Exception as e:
        logger.error(f"Error logging in: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/users/<user_id>', methods=['GET'])
@token_required
def get_user(user_id):
    """Get user information"""
    try:
        user = db.get_user_by_id(user_id)
        if user:
            return jsonify({
                "success": True,
                "user": {
                    "id": user['id'],
                    "name": user['name'],
                    "email": user['email'],
                    "role": user['role'],
                    "department": user.get('department')
                }
            })
        else:
            return jsonify({
                "success": False,
                "message": "User not found"
            }), 404
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==========================================
# BUTTON-BASED CHAT ENDPOINTS
# ==========================================

@app.route('/api/upload/image', methods=['POST'])
@token_required
def upload_image():
    """
    Upload an image to Cloudinary
    Accepts either multipart/form-data with 'image' file or JSON with base64 'image' data
    """
    try:
        user_id = request.user_id
        
        # Handle multipart form data (file upload)
        if 'image' in request.files:
            file = request.files['image']
            if file.filename == '':
                return jsonify({
                    "success": False,
                    "error": "No file selected"
                }), 400
            
            # Read file data
            file_data = file.read()
            filename = file.filename
            content_type = file.content_type or 'image/jpeg'
            
            result = cloudinary_service.upload_image(
                file_data=file_data,
                filename=filename,
                content_type=content_type,
                user_id=user_id
            )
        
        # Handle JSON with base64 encoded image
        elif request.is_json:
            data = request.json
            base64_image = data.get('image')
            filename = data.get('filename', 'upload.jpg')
            
            if not base64_image:
                return jsonify({
                    "success": False,
                    "error": "No image data provided"
                }), 400
            
            result = cloudinary_service.upload_base64_image(
                base64_data=base64_image,
                filename=filename,
                user_id=user_id
            )
        else:
            return jsonify({
                "success": False,
                "error": "Invalid request format. Send multipart/form-data or JSON with base64 image"
            }), 400
        
        if result['success']:
            return jsonify({
                "success": True,
                "url": result['url'],
                "public_id": result.get('public_id'),
                "message": "Image uploaded successfully"
            })
        else:
            return jsonify({
                "success": False,
                "error": result.get('error', 'Upload failed')
            }), 400
            
    except Exception as e:
        logger.error(f"Error uploading image: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/chat/categories', methods=['GET'])
@token_required
def get_chat_categories():
    """Get categories for button navigation"""
    try:
        categories = kb.get_categories_structure()
        return jsonify({
            "success": True,
            "categories": categories
        })
    except Exception as e:
        logger.error(f"Error getting categories: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/chat/solution/<subcat_id>', methods=['GET'])
@token_required
def get_solution(subcat_id):
    """Get solution for a specific subcategory"""
    try:
        solution = kb.get_solution_by_subcategory_id(subcat_id)
        if solution:
            # Increment view count in database
            try:
                db.increment_kb_views(subcat_id)
            except Exception:
                pass  # Non-critical, don't fail the request
            return jsonify({
                "success": True,
                "solution": solution
            })
        else:
            return jsonify({
                "success": False,
                "error": "Solution not found"
            }), 404
    except Exception as e:
        logger.error(f"Error getting solution: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/chat/create-ticket', methods=['POST'])
@token_required
def create_ticket_from_chat():
    """Create a ticket from chatbot interaction"""
    try:
        data = request.json
        category = data.get('category')
        subcategory = data.get('subcategory')
        subject = data.get('subject')
        description = data.get('description')
        session_id = data.get('session_id')
        attachment_urls = data.get('attachment_urls')  # Array of image URLs
        
        if not all([category, subject, description]):
            return jsonify({
                "success": False,
                "error": "category, subject, and description are required"
            }), 400
        
        # Create ticket
        ticket = db.create_ticket(
            user_id=request.user_id,
            user_name=request.user_name,
            user_email=request.user_email,
            category=category,
            subcategory=subcategory,
            subject=subject,
            description=description,
            session_id=session_id,
            attachment_urls=attachment_urls
        )
        
        if ticket:
            # Send auto-assignment emails if ticket was assigned (combined email)
            if ticket.get('assigned_to_id'):
                try:
                    tech_info = db.get_technician_by_id(ticket['assigned_to_id'])
                    if tech_info:
                        # Send single combined creation+assignment email to user
                        email_service.send_ticket_created_with_assignment(
                            user_email=request.user_email,
                            user_name=request.user_name,
                            ticket_id=ticket['id'],
                            category=category,
                            subject=subject,
                            description=description,
                            priority=ticket.get('priority', 'P3'),
                            technician_name=tech_info.get('name', ''),
                            technician_email=tech_info.get('email', '')
                        )
                        # Send separate notification to technician
                        email_service.send_technician_assignment(
                            tech_email=tech_info.get('email', ''),
                            tech_name=tech_info.get('name', ''),
                            ticket_id=ticket['id'],
                            user_name=request.user_name,
                            category=category,
                            subject=subject,
                            description=description,
                            priority=ticket.get('priority', 'P3')
                        )
                except Exception as assign_email_err:
                    logger.warning(f"Failed to send auto-assignment emails: {assign_email_err}")
            else:
                # No auto-assignment - send just the creation email
                try:
                    email_service.send_ticket_created(
                        user_email=request.user_email,
                        user_name=request.user_name,
                        ticket_id=ticket['id'],
                        category=category,
                        subject=subject,
                        description=description,
                        priority=ticket.get('priority', 'P3')
                    )
                except Exception as email_error:
                    logger.warning(f"Failed to send ticket creation email: {email_error}")
            
            return jsonify({
                "success": True,
                "ticket": dict(ticket),
                "message": f"Ticket {ticket['id']} created successfully"
            }), 201
        else:
            return jsonify({
                "success": False,
                "error": "Failed to create ticket"
            }), 500
    
    except Exception as e:
        logger.error(f"Error creating ticket: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/chat', methods=['POST'])
@token_required
def chat():
    """
    Main chat endpoint - handles button-based navigation through 6-level hierarchy
    Flow: Incident/Request → Smart Category → Category → Type → Item → Issue → Solution → Ticket
    """
    try:
        data = request.json
        message = data.get('message')
        session_id = data.get('session_id')
        action = data.get('action')
        attachment_urls = data.get('attachment_urls')
        
        # Get user info from token
        user_id = request.user_id
        user_email = request.user_email
        user_name = request.user_name
        
        # Create session if not provided
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())
        
        # Get or create conversation state
        state_key = f"{user_id}_{session_id}"
        if state_key not in conversation_states:
            conversation_states[state_key] = chat_handler.create_initial_state()
        
        conversation_state = conversation_states[state_key]
        
        # Store attachment_urls if provided
        if attachment_urls:
            conversation_state['attachment_urls'] = attachment_urls
        
        logger.info(f"Chat request: action={action}, state={conversation_state.get('state')}, session={session_id}")
        
        # Prepare user info for handler
        user_info = {
            'id': user_id,
            'email': user_email,
            'name': user_name
        }
        
        # If no action provided but message exists and state expects free text
        current_state = conversation_state.get('state', '')
        request_text_states = [
            'awaiting_free_text', 'request_justification', 'request_vpn_reason',
            'request_shared_folder_path', 'request_software_type', 'end_feedback_text'
        ]
        if not action and message and current_state in request_text_states:
            action = 'free_text'
        
        # Default to start if no action
        if not action:
            action = 'start'
        
        # Handle the action using the chat handler
        handler_response = chat_handler.handle_action(
            action=action,
            data=data,
            conversation_state=conversation_state,
            user_info=user_info
        )
        
        # Check if we need to go to start
        if handler_response.get('go_to_start'):
            handler_response = chat_handler.handle_action(
                action='start',
                data={},
                conversation_state=conversation_state,
                user_info=user_info
            )
        
        # Check if we need to create a ticket
        if handler_response.get('create_ticket'):
            ticket_data = handler_response.get('ticket_data', {})
            stored_attachment_urls = ticket_data.get('attachment_urls', []) or conversation_state.get('attachment_urls', [])
            
            # Create the ticket
            ticket = db.create_ticket(
                user_id=user_id,
                user_name=user_name,
                user_email=user_email,
                category=ticket_data.get('category', 'General'),
                subcategory=conversation_state.get('smart_category'),  # Store smart category
                subject=ticket_data.get('subject', 'Support Request'),
                description=ticket_data.get('description', 'User requested support'),
                session_id=session_id,
                attachment_urls=stored_attachment_urls if stored_attachment_urls else None
            )
            
            if ticket:
                conversation_state['ticket_id'] = ticket['id']
                
                # Send assignment emails if ticket was auto-assigned (combined email)
                assigned_tech_id = ticket.get('assigned_to_id')
                assigned_tech_name = ticket.get('assigned_to')
                if assigned_tech_id:
                    try:
                        tech_info = db.get_technician_by_id(assigned_tech_id)
                        if tech_info:
                            # Send single combined creation+assignment email to user
                            email_service.send_ticket_created_with_assignment(
                                user_email=user_email,
                                user_name=user_name,
                                ticket_id=ticket['id'],
                                category=ticket_data.get('category', 'General'),
                                subject=ticket_data.get('subject', 'Support Request'),
                                description=ticket_data.get('description', ''),
                                priority=ticket.get('priority', 'P3'),
                                technician_name=tech_info.get('name', 'Support Technician'),
                                technician_email=tech_info.get('email', '')
                            )
                            # Notify technician separately
                            email_service.send_technician_assignment(
                                tech_email=tech_info.get('email', ''),
                                tech_name=tech_info.get('name', ''),
                                ticket_id=ticket['id'],
                                user_name=user_name,
                                category=ticket_data.get('category', 'General'),
                                subject=ticket_data.get('subject', 'Support Request'),
                                description=ticket_data.get('description', ''),
                                priority=ticket.get('priority', 'P3')
                            )
                    except Exception as assign_email_err:
                        logger.warning(f"Failed to send auto-assignment emails: {assign_email_err}")
                else:
                    # No auto-assignment - send just the creation email
                    try:
                        email_service.send_ticket_created(
                            user_email=user_email,
                            user_name=user_name,
                            ticket_id=ticket['id'],
                            category=ticket_data.get('category', 'General'),
                            subject=ticket_data.get('subject', 'Support Request'),
                            description=ticket_data.get('description', ''),
                            priority=ticket.get('priority', 'P3')
                        )
                    except Exception as email_error:
                        logger.warning(f"Failed to send ticket creation email: {email_error}")
                
                # Check if this is a Request ticket with manager simulation
                if handler_response.get('simulate_manager_approval'):
                    # Simulate manager approval
                    simulated_manager = handler_response.get('simulated_manager', 'Your Manager')
                    
                    # Update ticket status to In Progress (manager approved)
                    try:
                        db.update_ticket_status(ticket['id'], 'In Progress', user_id, 'Manager Simulation',
                                               f"Manager approved by: {simulated_manager}")
                    except Exception as status_err:
                        logger.warning(f"Could not update ticket status: {status_err}")
                    
                    handler_response = {
                        "success": True,
                        "response": f"✅ **Request Approved!** (Ticket: **{ticket['id']}**)\n\n👤 **Manager {simulated_manager}** has reviewed and approved your request.\n\n📧 You will receive a confirmation email shortly.\n\n---\n\nWould you like to do anything else?",
                        "ticket_id": ticket['id'],
                        "buttons": [
                            {"id": "new", "label": "🆕 New Request", "action": "start", "value": "new"},
                            {"id": "done", "label": "✅ I'm Done", "action": "end", "value": "done"}
                        ],
                        "state": "manager_approved"
                    }
                    conversation_state['state'] = 'manager_approved'
                else:
                    # Build response with auto-assignment info + prompt star rating
                    assign_msg = ""
                    if ticket.get('assigned_to'):
                        assign_msg = f"\n\n👨‍💻 **Assigned to:** {ticket['assigned_to']} (auto-assigned based on shift availability)"
                    
                    # Trigger star rating flow so feedback saves with this ticket_id
                    conversation_state['state'] = 'end_rating'
                    star_ui = feedback_handler.get_star_rating_ui()
                    star_buttons = star_ui.get('buttons', [])
                    star_buttons.append({"id": "skip", "label": "⏭️ Skip Rating", "action": "skip_rating", "value": "skip"})
                    
                    handler_response = {
                        "success": True,
                        "response": f"🎫 **Ticket Created!**\n\n✅ I've created ticket **{ticket['id']}** for you.{assign_msg}\n\nOur support team will review it and get back to you soon.\n\n---\n\n📊 **How was your experience?** Please rate your interaction:",
                        "ticket_id": ticket['id'],
                        "show_star_rating": True,
                        "buttons": star_buttons,
                        "state": "end_rating"
                    }
            else:
                handler_response = {
                    "success": False,
                    "response": "Sorry, I couldn't create the ticket. Please try again.",
                    "buttons": [
                        {"id": "retry", "label": "🔄 Try Again", "action": "preview_ticket", "value": "retry"},
                        {"id": "back", "label": "⬅️ Start Over", "action": "start", "value": "back"}
                    ],
                    "state": conversation_state.get('state')
                }
        
        # Build final response
        response_data = {
            "success": handler_response.get('success', True),
            "session_id": session_id,
            "response": handler_response.get('response', ''),
            "buttons": handler_response.get('buttons', []),
            "show_text_input": handler_response.get('show_text_input', False),
            "show_attachment_upload": handler_response.get('show_attachment_upload', False),
            "show_star_rating": handler_response.get('show_star_rating', False),
            "show_checkboxes": handler_response.get('show_checkboxes', False),
            "checkboxes": handler_response.get('checkboxes', []),
            "state": handler_response.get('state', conversation_state.get('state', '')),
            "awaiting_confirmation": conversation_state.get('state') == 'awaiting_ticket_confirmation'
        }
        
        # Save feedback to database if ready
        if handler_response.get('feedback_data', {}).get('ready_to_save'):
            try:
                feedback_data = handler_response['feedback_data']
                feedback_data['session_id'] = session_id
                feedback_data['ticket_id'] = conversation_state.get('ticket_id')
                db.save_all_feedback(feedback_data)
                logger.info(f"Saved feedback for session {session_id}")
            except Exception as feedback_error:
                logger.warning(f"Failed to save feedback: {feedback_error}")
        
        if handler_response.get('ticket_id'):
            response_data['ticket_id'] = handler_response['ticket_id']
        
        # Include solutions_with_feedback for per-solution radio buttons
        if handler_response.get('solutions_with_feedback'):
            response_data['solutions_with_feedback'] = handler_response['solutions_with_feedback']
        
        # Save conversation state
        conversation_states[state_key] = conversation_state
        
        logger.info(f"Returning response with {len(response_data.get('buttons', []))} buttons, state={conversation_state.get('state')}")
        
        # Save to conversation history
        db.save_conversation(
            user_id=user_id,
            session_id=session_id,
            message_type='user' if message else 'action',
            message_content=message or action or 'start',
            buttons_shown=[b.get('label', '') for b in response_data.get('buttons', [])],
            button_clicked=action
        )
        
        return jsonify(response_data)
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e),
            "response": "Something went wrong. Please try again.",
            "buttons": [
                {"id": "restart", "label": "🔄 Start Over", "action": "start", "value": "restart"}
            ]
        }), 500


# ==========================================
# LEGACY CHAT ACTIONS (for backward compatibility)
# These handle old action types from the previous flow
# ==========================================
@app.route('/api/chat/legacy', methods=['POST'])
@token_required
def chat_legacy():
    """
    Legacy chat endpoint - handles old button-based and free-text interactions
    Kept for backward compatibility during transition
    """
    try:
        data = request.json
        message = data.get('message')
        session_id = data.get('session_id')
        action = data.get('action')  # 'select_category', 'select_subcategory', 'free_text', 'create_ticket', 'feedback'
        category = data.get('category')
        subcategory_id = data.get('subcategory_id')
        attachment_urls = data.get('attachment_urls')  # Array of image URLs for ticket attachments
        
        # Get user_id and email from token
        user_id = request.user_id
        user_email = request.user_email
        user_name = request.user_name
        
        # Create session if not provided
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())
        
        # Get or create conversation state
        state_key = f"{user_id}_{session_id}_legacy"
        conversation_state = conversation_states.get(state_key, {
            'state': 'initial',
            'selected_category': None,
            'selected_subcategory': None,
            'issue_description': None,
            'attachment_urls': []
        })
        
        # Store attachment_urls in conversation state if provided
        if attachment_urls:
            conversation_state['attachment_urls'] = attachment_urls
        
        logger.info(f"Legacy Chat request: action={action}, state_key={state_key}, current_state={conversation_state.get('state')}")
        
        response_data = {
            "success": True,
            "session_id": session_id,
            "buttons": [],
            "show_text_input": False,
            "awaiting_confirmation": False
        }
        
        # Handle different actions
        if action == 'start' or conversation_state['state'] == 'initial':
            # Show category buttons
            categories = kb.get_categories_structure()
            response_data["response"] = f"Hi {user_name}! 👋\n\nI'm Eve, your AI-powered IT chatbot, here to make things simple and easy for you. Whether you need help, answers, or just a little guidance, I'm always ready to assist.\n\nHow can I help you today? 😊\n\nIf you would like to report issues with applications not listed below, just ask! I will give you the option to connect with our support engineers if necessary."
            response_data["buttons"] = [
                {
                    "id": cat['id'],
                    "label": f"{cat['icon']} {cat['display_name']}",
                    "icon": cat['icon'],
                    "action": "select_category",
                    "value": cat['name']
                }
                for cat in categories
            ]
            conversation_state['state'] = 'awaiting_category'
        
        elif action == 'select_category':
            # User selected a category, show subcategories
            selected_cat = category or data.get('value')
            logger.info(f"select_category: selected_cat={selected_cat}")
            conversation_state['selected_category'] = selected_cat
            
            # Get subcategories for this category
            categories = kb.get_categories_structure()
            selected_category_data = next((c for c in categories if c['name'] == selected_cat), None)
            logger.info(f"select_category: found category data={selected_category_data is not None}")
            
            if selected_category_data:
                if selected_cat == 'Other':
                    # Free text mode for "Other Issues"
                    response_data["response"] = "Please describe your issue in detail. I'll help identify the appropriate category and find a solution for you:"
                    response_data["show_text_input"] = True
                    response_data["buttons"] = [
                        {"id": "back", "label": "⬅️ Back to Categories", "action": "go_back", "value": "back"}
                    ]
                    conversation_state['state'] = 'awaiting_free_text'
                else:
                    response_data["response"] = f"Please select your {selected_cat} issue:"
                    # Add subcategory buttons
                    response_data["buttons"] = [
                        {
                            "id": sub['id'],
                            "label": sub['title'],
                            "action": "select_subcategory",
                            "value": sub['id'],
                            "is_free_text": sub.get('is_free_text', False)
                        }
                        for sub in selected_category_data['subcategories']
                    ]
                    # Add "Other Issue" option for this category
                    response_data["buttons"].append({
                        "id": f"other_{selected_cat.lower()}",
                        "label": f"Other {selected_cat} Issue",
                        "action": "category_other",
                        "value": f"other_{selected_cat.lower()}",
                        "category": selected_cat
                    })
                    # Add back button
                    response_data["buttons"].append(
                        {"id": "back", "label": "⬅️ Back to Categories", "action": "go_back", "value": "back"}
                    )
                    conversation_state['state'] = 'awaiting_subcategory'
            else:
                response_data["response"] = "Category not found. Please try again."
                response_data["buttons"] = [
                    {"id": "back", "label": "⬅️ Back to Categories", "action": "go_back", "value": "back"}
                ]
        
        elif action == 'category_other':
            # User selected "Other Issue" within a category
            cat_from_data = data.get('category') or conversation_state.get('selected_category')
            conversation_state['selected_category'] = cat_from_data
            response_data["response"] = f"Please describe your {cat_from_data} issue in detail:"
            response_data["show_text_input"] = True
            response_data["buttons"] = [
                {"id": "back", "label": "⬅️ Back to Categories", "action": "go_back", "value": "back"}
            ]
            conversation_state['state'] = 'awaiting_category_free_text'
        
        elif action == 'go_back':
            # Go back to categories
            categories = kb.get_categories_structure()
            response_data["response"] = "What type of issue would you like help with?"
            response_data["buttons"] = [
                {
                    "id": cat['id'],
                    "label": cat['display_name'],
                    "icon": cat['icon'],
                    "action": "select_category",
                    "value": cat['name']
                }
                for cat in categories
            ]
            conversation_state['state'] = 'awaiting_category'
            conversation_state['selected_category'] = None
        
        elif action == 'select_subcategory':
            # User selected a subcategory, show solution
            subcat_id = subcategory_id or data.get('value')
            solution_data = kb.get_solution_by_subcategory_id(subcat_id)
            
            if solution_data:
                if solution_data.get('is_free_text'):
                    response_data["response"] = "Please describe your issue in detail:"
                    response_data["show_text_input"] = True
                    conversation_state['state'] = 'awaiting_free_text'
                else:
                    conversation_state['selected_subcategory'] = solution_data['title']
                    response_data["response"] = f"**{solution_data['title']}**\n\n{solution_data['solution']}\n\n---\n\nI can also create an incident on your behalf. Would you like me to create one?"
                    response_data["buttons"] = [
                        {"id": "yes", "label": "Yes", "action": "preview_ticket", "value": "yes"},
                        {"id": "no", "label": "No", "action": "decline_ticket", "value": "no"}
                    ]
                    response_data["awaiting_confirmation"] = True
                    conversation_state['state'] = 'awaiting_ticket_confirmation'
                    conversation_state['solution_shown'] = solution_data
            else:
                response_data["response"] = "Solution not found. Would you like to create a ticket?"
                response_data["buttons"] = [
                    {"id": "yes", "label": "Yes", "action": "preview_ticket", "value": "yes"},
                    {"id": "no", "label": "No", "action": "start", "value": "no"}
                ]
        
        elif action == 'preview_ticket':
            # Show ticket preview with AI-summarized content before creating
            solution_data = conversation_state.get('solution_shown', {})
            issue_history = conversation_state.get('issue_history', [])
            issue_description = conversation_state.get('issue_description', '')
            category = conversation_state.get('selected_category', 'Other')
            
            # Use orchestrator to summarize the conversation into subject and description
            try:
                if issue_history:
                    summary_result = run_async(orchestrator.summarize_for_ticket(
                        user_id=str(user_id),
                        session_id=conversation_state.get('session_id', f"session_{user_id}"),
                        conversation_history=issue_history,
                        category=category
                    ))
                    
                    subject = summary_result.get('subject', 'Support Request')
                    description = summary_result.get('description', '\n'.join(issue_history))
                    
                    logger.info(f"Orchestrator summarized ticket - Subject: {subject[:50]}...")
                else:
                    # Fallback for no history
                    subject = issue_description[:100] if issue_description else 'Support Request'
                    description = issue_description or 'User requested support'
                    
            except Exception as e:
                logger.warning(f"Orchestrator summarization failed, using fallback: {e}")
                # Fallback to simple extraction
                if issue_history:
                    subject = issue_history[0][:100] if issue_history[0] else "Support Request"
                    description = "\n".join(issue_history)
                else:
                    subject = solution_data.get('title', issue_description[:100] if issue_description else 'Support Request')
                    description = issue_description or solution_data.get('title', 'User requested support')
            
            # Store the prepared ticket data
            conversation_state['prepared_ticket'] = {
                'subject': subject,
                'description': description,
                'category': category
            }
            
            # Show preview
            preview = f"""📋 **Ticket Preview**

**Category:** {category}

**Subject:** {subject}

**Description:**
{description}

---
✅ Please confirm if you'd like to create this ticket."""
            
            response_data["response"] = preview
            response_data["buttons"] = [
                {"id": "yes", "label": "✅ Confirm & Create Ticket", "action": "confirm_ticket", "value": "yes"},
                {"id": "edit", "label": "✏️ Add More Details", "action": "add_details", "value": "edit"},
                {"id": "no", "label": "❌ Cancel", "action": "decline_ticket", "value": "no"}
            ]
            conversation_state['state'] = 'awaiting_ticket_confirmation'
        
        elif action == 'add_details':
            # User wants to add more details before creating ticket
            response_data["response"] = "Please provide any additional details you'd like to include in the ticket:"
            response_data["show_text_input"] = True
            response_data["buttons"] = [
                {"id": "done", "label": "✅ Done, Show Preview", "action": "preview_ticket", "value": "done"},
                {"id": "cancel", "label": "❌ Cancel", "action": "decline_ticket", "value": "cancel"}
            ]
            conversation_state['state'] = 'adding_ticket_details'
        
        elif action == 'confirm_ticket':
            # User confirmed - create the ticket with prepared data
            prepared_ticket = conversation_state.get('prepared_ticket', {})
            solution_data = conversation_state.get('solution_shown', {})
            issue_history = conversation_state.get('issue_history', [])
            stored_attachment_urls = conversation_state.get('attachment_urls', [])
            
            # Get ticket details from prepared data or fallback
            if prepared_ticket:
                subject = prepared_ticket.get('subject', 'Support Request')
                description = prepared_ticket.get('description', 'User requested support')
                category = prepared_ticket.get('category', 'Other')
            else:
                # Fallback - build from history
                issue_description = conversation_state.get('issue_description', '')
                if issue_history:
                    description = "\n".join(issue_history)
                    subject = issue_history[0][:100] if issue_history else 'Support Request'
                else:
                    description = issue_description or solution_data.get('title', 'User requested support')
                    subject = solution_data.get('title', issue_description[:100] if issue_description else 'Support Request')
                category = conversation_state.get('selected_category', 'Other')
            
            ticket = db.create_ticket(
                user_id=user_id,
                user_name=user_name,
                user_email=user_email,
                category=category,
                subcategory=conversation_state.get('selected_subcategory'),
                subject=subject,
                description=description,
                session_id=session_id,
                attachment_urls=stored_attachment_urls if stored_attachment_urls else None
            )
            
            if ticket:
                # Send email notification for ticket creation
                try:
                    email_service.send_ticket_created(
                        user_email=user_email,
                        user_name=user_name,
                        ticket_id=ticket['id'],
                        category=category,
                        subject=subject,
                        description=description,
                        priority=ticket.get('priority', 'P3')
                    )
                except Exception as email_error:
                    logger.warning(f"Failed to send ticket creation email: {email_error}")
                
                response_data["response"] = f"🎫 **{ticket['id']}**\n\n✅ I've created ticket **{ticket['id']}** for you.\n\nOur support team will review it and get back to you soon.\n\nIs there anything else I can help you with?"
                response_data["ticket_id"] = ticket['id']
                response_data["buttons"] = [
                    {"id": "new", "label": "🆕 New Issue", "action": "start", "value": "new"},
                    {"id": "done", "label": "✅ I'm Done", "action": "end", "value": "done"}
                ]
                conversation_state['state'] = 'ticket_created'
            else:
                response_data["response"] = "Sorry, I couldn't create the ticket. Please try again or contact support directly."
                response_data["buttons"] = [
                    {"id": "retry", "label": "🔄 Try Again", "action": "confirm_ticket", "value": "retry"},
                    {"id": "back", "label": "⬅️ Back to Categories", "action": "start", "value": "back"}
                ]
        
        elif action == 'decline_ticket':
            # User doesn't want a ticket
            response_data["response"] = "No problem! Is there anything else I can help you with?"
            response_data["buttons"] = [
                {"id": "new", "label": "🆕 New Issue", "action": "start", "value": "new"},
                {"id": "done", "label": "✅ I'm Done", "action": "end", "value": "done"}
            ]
            conversation_state['state'] = 'completed'
        
        elif action == 'end':
            response_data["response"] = "Thank you for using IT Support! Have a great day! 👋"
            response_data["buttons"] = [
                {"id": "new", "label": "🆕 Start New Conversation", "action": "start", "value": "new"}
            ]
            conversation_state['state'] = 'ended'
        
        elif conversation_state.get('state') == 'adding_ticket_details' and message:
            # User is adding more details to ticket - add to history and show updated preview
            if 'issue_history' not in conversation_state:
                conversation_state['issue_history'] = []
            conversation_state['issue_history'].append(message)
            
            # Re-generate preview with new details
            issue_history = conversation_state['issue_history']
            category = conversation_state.get('selected_category', 'Other')
            
            # Use orchestrator to summarize the conversation into subject and description
            try:
                summary_result = run_async(orchestrator.summarize_for_ticket(
                    user_id=str(user_id),
                    session_id=conversation_state.get('session_id', f"session_{user_id}"),
                    conversation_history=issue_history,
                    category=category
                ))
                
                subject = summary_result.get('subject', 'Support Request')
                description = summary_result.get('description', '\n'.join(issue_history))
                
                logger.info(f"Orchestrator re-summarized ticket - Subject: {subject[:50]}...")
            except Exception as e:
                logger.warning(f"Orchestrator summarization failed, using fallback: {e}")
                subject = issue_history[0][:100] if issue_history[0] else "Support Request"
                description = "\n".join(issue_history)
            
            # Store the prepared ticket data
            conversation_state['prepared_ticket'] = {
                'subject': subject,
                'description': description,
                'category': category
            }
            
            # Show updated preview
            preview = f"""📋 **Updated Ticket Preview**

**Category:** {category}

**Subject:** {subject}

**Description:**
{description}

---
✅ Please confirm if you'd like to create this ticket."""
            
            response_data["response"] = preview
            response_data["buttons"] = [
                {"id": "yes", "label": "✅ Confirm & Create Ticket", "action": "confirm_ticket", "value": "yes"},
                {"id": "edit", "label": "✏️ Add More Details", "action": "add_details", "value": "edit"},
                {"id": "no", "label": "❌ Cancel", "action": "decline_ticket", "value": "no"}
            ]
            conversation_state['state'] = 'awaiting_ticket_confirmation'
        
        elif action == 'free_text' or conversation_state['state'] in ['awaiting_free_text', 'awaiting_category_free_text', 'awaiting_agent_response']:
            # Handle free text input using AI Agent
            if message:
                conversation_state['issue_description'] = message
                
                # Track conversation history for better ticket context
                if 'issue_history' not in conversation_state:
                    conversation_state['issue_history'] = []
                conversation_state['issue_history'].append(message)
                
                # Check if category was provided (from "Other Issue" within category)
                provided_category = data.get('category') or conversation_state.get('selected_category')
                
                # If no category, try to auto-detect from the message
                detected_category = None
                if not provided_category or provided_category == 'Other':
                    # Auto-detect category based on keywords
                    message_lower = message.lower()
                    category_keywords = {
                        'VPN': ['vpn', 'remote', 'connect remotely', 'work from home', 'pulse secure', 'cisco anyconnect'],
                        'Email': ['email', 'outlook', 'mail', 'inbox', 'spam', 'phishing', 'calendar invite'],
                        'Network': ['network', 'internet', 'wifi', 'ethernet', 'connection', 'slow internet', 'no internet'],
                        'Hardware': ['laptop', 'computer', 'keyboard', 'mouse', 'monitor', 'printer', 'hardware', 'screen', 'battery'],
                        'Software': ['software', 'install', 'application', 'app', 'crash', 'update', 'license', 'download'],
                        'Account': ['password', 'login', 'account', 'locked', 'reset', 'access', 'permission', 'mfa', '2fa'],
                        'Windows': ['windows', 'blue screen', 'bsod', 'restart', 'shutdown', 'update', 'slow pc'],
                        'Zoom': ['zoom', 'teams', 'meeting', 'video call', 'audio', 'microphone', 'camera', 'screen share']
                    }
                    
                    for cat, keywords in category_keywords.items():
                        if any(kw in message_lower for kw in keywords):
                            detected_category = cat
                            break
                    
                    if detected_category:
                        conversation_state['selected_category'] = detected_category
                        provided_category = detected_category
                    else:
                        # Default to 'Other' if no match
                        conversation_state['selected_category'] = 'Other'
                        provided_category = 'Other'
                
                # Get or initialize the agent conversation state
                agent_state = conversation_state.get('agent_state')
                
                try:
                    # Use the AI Agent to process the message
                    logger.info(f"Processing free text with AI agent for user {user_id}")
                    
                    agent_result = run_async(orchestrator.handle_user_query(
                        user_id=user_id,
                        user_email=user_email,
                        session_id=session_id,
                        message=message,
                        conversation_state=agent_state
                    ))
                    
                    # Store updated agent state
                    conversation_state['agent_state'] = agent_result.get('conversation_state')
                    
                    # Get the agent's response
                    agent_response = agent_result.get('response', '')
                    
                    # Check if agent needs escalation (wants to create a ticket)
                    if agent_result.get('escalated') or 'ESCALATE_TO_HUMAN:' in agent_response:
                        # Parse out the escalation marker if present
                        if 'ESCALATE_TO_HUMAN:' in agent_response:
                            parts = agent_response.split('ESCALATE_TO_HUMAN:', 1)
                            display_response = parts[0].strip()
                            escalation_summary = parts[1].strip() if len(parts) > 1 else message
                            conversation_state['escalation_summary'] = escalation_summary
                        else:
                            display_response = agent_response
                        
                        response_data["response"] = display_response + "\n\nWould you like me to create a support ticket for this issue?"
                        response_data["buttons"] = [
                            {"id": "yes", "label": "✅ Yes, Create Ticket", "action": "preview_ticket", "value": "yes"},
                            {"id": "no", "label": "❌ No, Thanks", "action": "decline_ticket", "value": "no"}
                        ]
                        conversation_state['state'] = 'awaiting_ticket_confirmation'
                    
                    # Check if agent is awaiting confirmation (ticket preview shown)
                    elif agent_result.get('awaiting_confirmation'):
                        response_data["response"] = agent_response
                        response_data["buttons"] = [
                            {"id": "yes", "label": "✅ Confirm & Create Ticket", "action": "agent_confirm_ticket", "value": "yes"},
                            {"id": "no", "label": "❌ Cancel", "action": "decline_ticket", "value": "no"}
                        ]
                        conversation_state['state'] = 'awaiting_agent_confirmation'
                    
                    # Check if agent is asking for clarification
                    elif agent_result.get('needs_clarification'):
                        response_data["response"] = agent_response
                        response_data["show_text_input"] = True
                        response_data["buttons"] = [
                            {"id": "skip", "label": "⏭️ Skip to Ticket Creation", "action": "preview_ticket", "value": "skip"},
                            {"id": "back", "label": "⬅️ Back to Categories", "action": "go_back", "value": "back"}
                        ]
                        conversation_state['state'] = 'awaiting_agent_response'
                    
                    # Check if ticket was created
                    elif agent_result.get('ticket_id'):
                        response_data["response"] = f"✅ I've created ticket **#{agent_result['ticket_id']}** for you.\n\nOur support team will review it and get back to you soon.\n\nIs there anything else I can help you with?"
                        response_data["ticket_id"] = agent_result['ticket_id']
                        response_data["buttons"] = [
                            {"id": "new", "label": "🆕 New Issue", "action": "start", "value": "new"},
                            {"id": "done", "label": "✅ I'm Done", "action": "end", "value": "done"}
                        ]
                        conversation_state['state'] = 'ticket_created'
                    
                    # Agent provided a solution - ask if it helped
                    else:
                        response_data["response"] = agent_response + "\n\n---\n\nDid this help resolve your issue?"
                        response_data["buttons"] = [
                            {"id": "yes", "label": "✅ Yes, Solved!", "action": "decline_ticket", "value": "solved"},
                            {"id": "no", "label": "❌ No, Need More Help", "action": "agent_continue", "value": "more"},
                            {"id": "ticket", "label": "🎫 Create Ticket", "action": "preview_ticket", "value": "ticket"}
                        ]
                        response_data["show_text_input"] = True  # Allow follow-up questions
                        conversation_state['state'] = 'awaiting_agent_response'
                    
                    logger.info(f"AI agent responded successfully for user {user_id}")
                    
                except Exception as agent_error:
                    logger.error(f"AI Agent error: {agent_error}")
                    import traceback
                    logger.error(traceback.format_exc())
                    
                    # Fallback to basic KB search if agent fails
                    logger.info("Falling back to basic KB search")
                    results = kb.search(message, top_k=1)
                    
                    if results and results[0].get('confidence', 0) > 0.7:
                        result = results[0]
                        response_data["response"] = f"I found a solution that might help:\n\n**{result['issue']}**\n\n{result['solution']}\n\n---\n\nDid this solve your issue?"
                        response_data["buttons"] = [
                            {"id": "yes", "label": "✅ Yes, Solved!", "action": "decline_ticket", "value": "solved"},
                            {"id": "no", "label": "❌ No, Create Ticket", "action": "preview_ticket", "value": "create"}
                        ]
                        conversation_state['solution_shown'] = result
                        conversation_state['state'] = 'awaiting_feedback'
                    else:
                        response_data["response"] = "I couldn't find an exact solution for your issue. Would you like me to create a support ticket?"
                        response_data["buttons"] = [
                            {"id": "yes", "label": "Yes, Create Ticket", "action": "preview_ticket", "value": "yes"},
                            {"id": "no", "label": "No, Thanks", "action": "decline_ticket", "value": "no"}
                        ]
                        conversation_state['state'] = 'awaiting_ticket_confirmation'
            else:
                response_data["response"] = "Please describe your issue:"
                response_data["show_text_input"] = True
        
        elif action == 'agent_continue':
            # User wants more help from the agent - continue the conversation
            response_data["response"] = "Please provide more details or ask a follow-up question:"
            response_data["show_text_input"] = True
            response_data["buttons"] = [
                {"id": "ticket", "label": "🎫 Create Ticket Instead", "action": "preview_ticket", "value": "ticket"},
                {"id": "back", "label": "⬅️ Back to Categories", "action": "go_back", "value": "back"}
            ]
            conversation_state['state'] = 'awaiting_agent_response'
        
        elif action == 'agent_confirm_ticket':
            # Handle agent-initiated ticket confirmation
            agent_state = conversation_state.get('agent_state')
            
            try:
                agent_result = run_async(orchestrator.handle_user_query(
                    user_id=user_id,
                    user_email=user_email,
                    session_id=session_id,
                    message="yes",  # Confirm the ticket
                    conversation_state=agent_state
                ))
                
                conversation_state['agent_state'] = agent_result.get('conversation_state')
                
                if agent_result.get('ticket_id'):
                    response_data["response"] = f"✅ I've created ticket **#{agent_result['ticket_id']}** for you.\n\nOur support team will review it and get back to you soon.\n\nIs there anything else I can help you with?"
                    response_data["ticket_id"] = agent_result['ticket_id']
                    response_data["buttons"] = [
                        {"id": "new", "label": "🆕 New Issue", "action": "start", "value": "new"},
                        {"id": "done", "label": "✅ I'm Done", "action": "end", "value": "done"}
                    ]
                    conversation_state['state'] = 'ticket_created'
                else:
                    response_data["response"] = agent_result.get('response', 'Ticket creation in progress...')
                    response_data["buttons"] = [
                        {"id": "new", "label": "🆕 New Issue", "action": "start", "value": "new"},
                        {"id": "done", "label": "✅ I'm Done", "action": "end", "value": "done"}
                    ]
            except Exception as e:
                logger.error(f"Error in agent ticket confirmation: {e}")
                # Fallback to regular ticket creation
                response_data["response"] = "There was an issue with the AI assistant. Let me create the ticket for you directly."
                response_data["buttons"] = [
                    {"id": "yes", "label": "✅ Create Ticket", "action": "preview_ticket", "value": "yes"},
                    {"id": "no", "label": "❌ Cancel", "action": "decline_ticket", "value": "no"}
                ]
                conversation_state['state'] = 'awaiting_ticket_confirmation'
        
        else:
            # Default: show categories
            categories = kb.get_categories_structure()
            response_data["response"] = "How can I help you today?"
            response_data["buttons"] = [
                {
                    "id": cat['id'],
                    "label": f"{cat['icon']} {cat['display_name']}",
                    "action": "select_category",
                    "value": cat['name']
                }
                for cat in categories
            ]
            conversation_state['state'] = 'awaiting_category'
        
        # Save conversation state
        conversation_states[state_key] = conversation_state
        
        logger.info(f"Returning response with {len(response_data.get('buttons', []))} buttons")
        if response_data.get('buttons'):
            logger.info(f"Button actions: {[b.get('action') for b in response_data['buttons']]}")
        
        # Save to conversation history
        db.save_conversation(
            user_id=user_id,
            session_id=session_id,
            message_type='user' if message else 'action',
            message_content=message or action or 'start',
            buttons_shown=[b['label'] for b in response_data.get('buttons', [])],
            button_clicked=action
        )
        
        return jsonify(response_data)
    
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/chat/reset', methods=['POST'])
@token_required
def reset_conversation():
    """Reset conversation state for a session"""
    try:
        data = request.json
        session_id = data.get('session_id')
        user_id = request.user_id
        
        if session_id:
            state_key = f"{user_id}_{session_id}"
            if state_key in conversation_states:
                del conversation_states[state_key]
                logger.info(f"Reset conversation state for {state_key}")
        
        return jsonify({
            "success": True,
            "message": "Conversation reset successfully"
        })
    
    except Exception as e:
        logger.error(f"Error resetting conversation: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==========================================
# TICKET ENDPOINTS
# ==========================================

@app.route('/api/tickets/user/<user_id>', methods=['GET'])
@token_required
def get_user_tickets(user_id):
    """Get all tickets for a specific user"""
    try:
        # Verify user is requesting their own tickets or is admin
        if request.user_id != user_id and request.user_role != 'admin':
            return jsonify({
                "success": False,
                "error": "Unauthorized"
            }), 403
        
        tickets = db.get_user_tickets(user_id)
        ticket_list = [dict(ticket) for ticket in tickets] if tickets else []
        
        # Attach solution feedback to each ticket
        for t in ticket_list:
            try:
                feedback_rows = db.get_helpful_solutions_for_ticket(t['id'])
                if feedback_rows:
                    t['solution_feedback'] = [
                        {
                            'index': row['solution_index'],
                            'text': row['solution_text'],
                            'feedback_type': row['feedback_type']
                        }
                        for row in feedback_rows
                    ]
                else:
                    t['solution_feedback'] = []
            except Exception:
                t['solution_feedback'] = []
        
        return jsonify({
            "success": True,
            "tickets": ticket_list
        })
    except Exception as e:
        logger.error(f"Error getting user tickets: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/tickets', methods=['GET'])
@token_required
def get_all_tickets():
    """Get all tickets with optional filters"""
    try:
        status = request.args.get('status')
        priority = request.args.get('priority')
        category = request.args.get('category')
        limit = request.args.get('limit', 100, type=int)
        
        tickets = db.get_all_tickets(status=status, priority=priority, category=category, limit=limit)
        ticket_list = [dict(ticket) for ticket in tickets] if tickets else []
        
        # Attach solution feedback to each ticket
        for t in ticket_list:
            try:
                feedback_rows = db.get_helpful_solutions_for_ticket(t['id'])
                if feedback_rows:
                    t['solution_feedback'] = [
                        {
                            'index': row['solution_index'],
                            'text': row['solution_text'],
                            'feedback_type': row['feedback_type']
                        }
                        for row in feedback_rows
                    ]
                else:
                    t['solution_feedback'] = []
            except Exception:
                t['solution_feedback'] = []
        
        return jsonify({
            "success": True,
            "tickets": ticket_list
        })
    except Exception as e:
        logger.error(f"Error getting all tickets: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/tickets/<ticket_id>', methods=['GET'])
@token_required
def get_ticket(ticket_id):
    """Get specific ticket details"""
    try:
        ticket = db.get_ticket_by_id(ticket_id)
        if ticket:
            # Verify user owns ticket or is admin
            if request.user_id != ticket['user_id'] and request.user_role != 'admin':
                return jsonify({
                    "success": False,
                    "error": "Unauthorized"
                }), 403
            
            ticket_dict = dict(ticket)
            
            # Include solution feedback
            try:
                feedback_rows = db.get_helpful_solutions_for_ticket(ticket_id)
                if feedback_rows:
                    ticket_dict['solution_feedback'] = [
                        {
                            'index': row['solution_index'],
                            'text': row['solution_text'],
                            'feedback_type': row['feedback_type']
                        }
                        for row in feedback_rows
                    ]
                else:
                    ticket_dict['solution_feedback'] = []
            except Exception:
                ticket_dict['solution_feedback'] = []
            
            return jsonify({
                "success": True,
                "ticket": ticket_dict
            })
        else:
            return jsonify({
                "success": False,
                "message": "Ticket not found"
            }), 404
    except Exception as e:
        logger.error(f"Error getting ticket: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/tickets/<ticket_id>/status', methods=['PUT'])
@token_required
def update_ticket_status(ticket_id):
    """Update ticket status"""
    try:
        data = request.json
        status = data.get('status')
        resolution_notes = data.get('resolution_notes')
        
        if not status:
            return jsonify({
                "success": False,
                "error": "status is required"
            }), 400
        
        # Get the old ticket status before updating
        old_ticket = db.get_ticket_by_id(ticket_id)
        old_status = old_ticket['status'] if old_ticket else 'Unknown'
        
        ticket = db.update_ticket_status(
            ticket_id, 
            status, 
            user_id=request.user_id, 
            user_name=request.user_name,
            resolution_notes=resolution_notes
        )
        
        if ticket:
            # Send email notification to user about status change
            if old_status != status:
                try:
                    # Get user email from ticket
                    user_email = ticket.get('user_email') or old_ticket.get('user_email')
                    user_name = ticket.get('user_name') or old_ticket.get('user_name', 'User')
                    subject = ticket.get('subject') or old_ticket.get('subject', 'Your ticket')
                    
                    if user_email:
                        email_service.send_ticket_status_updated(
                            user_email=user_email,
                            user_name=user_name,
                            ticket_id=ticket_id,
                            subject=subject,
                            old_status=old_status,
                            new_status=status,
                            resolution_notes=resolution_notes
                        )
                except Exception as email_error:
                    logger.warning(f"Failed to send status update email: {email_error}")
            
            return jsonify({
                "success": True,
                "ticket": dict(ticket),
                "message": f"Ticket {ticket_id} updated successfully"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Ticket not found"
            }), 404
    except Exception as e:
        logger.error(f"Error updating ticket: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/tickets/<ticket_id>/assign', methods=['PUT'])
@admin_required
def assign_ticket(ticket_id):
    """Assign ticket to a technician"""
    try:
        data = request.json
        tech_id = data.get('technician_id')
        
        if not tech_id:
            return jsonify({
                "success": False,
                "error": "technician_id is required"
            }), 400
        
        # Get the ticket and technician info before assignment
        old_ticket = db.get_ticket_by_id(ticket_id)
        technician = db.get_technician_by_id(tech_id)
        
        ticket = db.assign_ticket(
            ticket_id, 
            tech_id,
            assigner_id=request.user_id,
            assigner_name=request.user_name
        )
        
        if ticket:
            # Send email notifications
            try:
                if old_ticket and technician:
                    user_email = old_ticket.get('user_email')
                    user_name = old_ticket.get('user_name', 'User')
                    subject = old_ticket.get('subject', 'Your ticket')
                    tech_name = technician.get('name', 'Support Technician')
                    tech_email = technician.get('email', '')
                    
                    # Notify user that technician was assigned
                    if user_email:
                        email_service.send_ticket_assigned(
                            user_email=user_email,
                            user_name=user_name,
                            ticket_id=ticket_id,
                            subject=subject,
                            technician_name=tech_name,
                            technician_email=tech_email
                        )
                    
                    # Notify technician about the new assignment
                    if tech_email:
                        email_service.send_technician_assignment(
                            tech_email=tech_email,
                            tech_name=tech_name,
                            ticket_id=ticket_id,
                            user_name=user_name,
                            category=old_ticket.get('category', 'General'),
                            subject=subject,
                            description=old_ticket.get('description', ''),
                            priority=old_ticket.get('priority', 'P3')
                        )
            except Exception as email_error:
                logger.warning(f"Failed to send assignment emails: {email_error}")
            
            return jsonify({
                "success": True,
                "ticket": dict(ticket),
                "message": f"Ticket assigned successfully"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to assign ticket"
            }), 400
    except Exception as e:
        logger.error(f"Error assigning ticket: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==========================================
# TECHNICIAN ENDPOINTS
# ==========================================

def serialize_technician(tech):
    """Convert technician record to JSON-serializable dict"""
    tech_dict = dict(tech)
    # Convert time objects to strings for JSON serialization
    if 'shift_start' in tech_dict and tech_dict['shift_start'] is not None:
        tech_dict['shift_start'] = str(tech_dict['shift_start'])
    if 'shift_end' in tech_dict and tech_dict['shift_end'] is not None:
        tech_dict['shift_end'] = str(tech_dict['shift_end'])
    # Convert date objects to strings
    if 'joined_date' in tech_dict and tech_dict['joined_date'] is not None:
        tech_dict['joined_date'] = str(tech_dict['joined_date'])
    # Datetime fields: let Flask's UTCJSONProvider handle them via jsonify
    # No need to manually convert — just ensure they're datetime objects (not pre-converted strings)
    return tech_dict

@app.route('/api/technicians', methods=['GET'])
@token_required
def get_technicians():
    """Get all technicians"""
    try:
        active_only = request.args.get('active', 'false').lower() == 'true'
        if active_only:
            technicians = db.get_active_technicians()
        else:
            technicians = db.get_all_technicians()
        return jsonify({
            "success": True,
            "technicians": [serialize_technician(t) for t in technicians] if technicians else []
        })
    except Exception as e:
        logger.error(f"Error getting technicians: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/technicians/<tech_id>', methods=['GET'])
@token_required
def get_technician(tech_id):
    """Get technician by ID"""
    try:
        tech = db.get_technician_by_id(tech_id)
        if tech:
            return jsonify({
                "success": True,
                "technician": serialize_technician(tech)
            })
        else:
            return jsonify({
                "success": False,
                "error": "Technician not found"
            }), 404
    except Exception as e:
        logger.error(f"Error getting technician: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/technicians', methods=['POST'])
@admin_required
def create_technician():
    """Create a new technician"""
    try:
        data = request.json
        name = data.get('name')
        email = data.get('email')
        role = data.get('role')
        department = data.get('department', 'IT Support')
        specialization = data.get('specialization')
        shift_start = data.get('shift_start')
        shift_end = data.get('shift_end')
        
        if not all([name, email, role]):
            return jsonify({
                "success": False,
                "error": "name, email, and role are required"
            }), 400
        
        tech = db.create_technician(name, email, role, department, specialization, shift_start=shift_start, shift_end=shift_end)
        if tech:
            return jsonify({
                "success": True,
                "technician": serialize_technician(tech)
            }), 201
        else:
            return jsonify({
                "success": False,
                "error": "Failed to create technician"
            }), 500
    except Exception as e:
        logger.error(f"Error creating technician: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/technicians/<tech_id>', methods=['PUT'])
@admin_required
def update_technician(tech_id):
    """Update technician"""
    try:
        data = request.json
        tech = db.update_technician(tech_id, **data)
        if tech:
            return jsonify({
                "success": True,
                "technician": serialize_technician(tech)
            })
        else:
            return jsonify({
                "success": False,
                "error": "Technician not found"
            }), 404
    except Exception as e:
        logger.error(f"Error updating technician: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/technicians/<tech_id>', methods=['DELETE'])
@admin_required
def delete_technician(tech_id):
    """Delete a technician"""
    try:
        tech = db.get_technician_by_id(tech_id)
        if not tech:
            return jsonify({
                "success": False,
                "error": "Technician not found"
            }), 404
        
        db.delete_technician(tech_id)
        return jsonify({
            "success": True,
            "message": f"Technician {tech['name']} deleted successfully"
        })
    except Exception as e:
        logger.error(f"Error deleting technician: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==========================================
# SLA ENDPOINTS
# ==========================================

@app.route('/api/sla', methods=['GET'])
@token_required
def get_sla_config():
    """Get SLA configuration"""
    try:
        sla = db.get_sla_config()
        return jsonify({
            "success": True,
            "sla_config": [dict(s) for s in sla] if sla else []
        })
    except Exception as e:
        logger.error(f"Error getting SLA config: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/sla/<sla_id>', methods=['PUT'])
@admin_required
def update_sla_config(sla_id):
    """Update SLA configuration"""
    try:
        data = request.json
        sla_hours = data.get('sla_hours')
        description = data.get('description')
        
        if sla_hours is None:
            return jsonify({
                "success": False,
                "error": "sla_hours is required"
            }), 400
        
        sla = db.update_sla_config(sla_id, sla_hours, description)
        if sla:
            return jsonify({
                "success": True,
                "sla_config": dict(sla)
            })
        else:
            return jsonify({
                "success": False,
                "error": "SLA config not found"
            }), 404
    except Exception as e:
        logger.error(f"Error updating SLA config: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/sla/breached', methods=['GET'])
@token_required
def get_sla_breached_tickets():
    """Get tickets that have breached SLA"""
    try:
        # First check and update SLA breaches
        db.check_and_update_sla_breaches()
        tickets = db.get_sla_breached_tickets()
        return jsonify({
            "success": True,
            "tickets": [dict(t) for t in tickets] if tickets else []
        })
    except Exception as e:
        logger.error(f"Error getting SLA breached tickets: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==========================================
# PRIORITY RULES ENDPOINTS
# ==========================================

@app.route('/api/priority-rules', methods=['GET'])
@token_required
def get_priority_rules():
    """Get all priority rules"""
    try:
        rules = db.get_priority_rules()
        return jsonify({
            "success": True,
            "rules": [dict(r) for r in rules] if rules else []
        })
    except Exception as e:
        logger.error(f"Error getting priority rules: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/priority-rules', methods=['POST'])
@admin_required
def create_priority_rule():
    """Create a new priority rule"""
    try:
        data = request.json
        keyword = data.get('keyword')
        priority = data.get('priority')
        category = data.get('category')
        
        if not all([keyword, priority]):
            return jsonify({
                "success": False,
                "error": "keyword and priority are required"
            }), 400
        
        rule = db.create_priority_rule(keyword, priority, category)
        if rule:
            return jsonify({
                "success": True,
                "rule": dict(rule)
            }), 201
        else:
            return jsonify({
                "success": False,
                "error": "Failed to create priority rule"
            }), 500
    except Exception as e:
        logger.error(f"Error creating priority rule: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/priority-rules/<rule_id>', methods=['DELETE'])
@admin_required
def delete_priority_rule(rule_id):
    """Delete a priority rule"""
    try:
        db.delete_priority_rule(rule_id)
        return jsonify({
            "success": True,
            "message": "Priority rule deleted"
        })
    except Exception as e:
        logger.error(f"Error deleting priority rule: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==========================================
# KNOWLEDGE BASE ENDPOINTS
# ==========================================

@app.route('/api/knowledge-base', methods=['GET'])
@token_required
def get_kb_articles():
    """Get all knowledge base articles"""
    try:
        # Get from PostgreSQL for admin management
        articles = db.get_all_kb_articles()
        return jsonify({
            "success": True,
            "articles": [dict(a) for a in articles] if articles else []
        })
    except Exception as e:
        logger.error(f"Error getting KB articles: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/knowledge-base/<article_id>', methods=['GET'])
@token_required
def get_kb_article(article_id):
    """Get a specific KB article"""
    try:
        article = db.get_kb_article_by_id(article_id)
        if article:
            db.increment_kb_views(article_id)
            return jsonify({
                "success": True,
                "article": dict(article)
            })
        else:
            return jsonify({
                "success": False,
                "error": "Article not found"
            }), 404
    except Exception as e:
        logger.error(f"Error getting KB article: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/knowledge-base', methods=['POST'])
@admin_required
def create_kb_article():
    """Create a new KB article"""
    try:
        data = request.json
        title = data.get('title')
        category = data.get('category')
        solution = data.get('solution')
        subcategory = data.get('subcategory')
        keywords = data.get('keywords')
        source = data.get('source')
        
        if not all([title, category, solution]):
            return jsonify({
                "success": False,
                "error": "title, category, and solution are required"
            }), 400
        
        # Add to PostgreSQL
        article = db.create_kb_article(
            title=title,
            category=category,
            solution=solution,
            subcategory=subcategory,
            keywords=keywords,
            author=request.user_name,
            source=source
        )
        
        # Also add to ChromaDB for semantic search
        if article:
            kb.add_entry(
                issue=title,
                solution=solution,
                source=source or 'Admin Created',
                entry_id=article['id'],
                category=category,
                subcategory=subcategory,
                keywords=keywords
            )
        
        if article:
            return jsonify({
                "success": True,
                "article": dict(article)
            }), 201
        else:
            return jsonify({
                "success": False,
                "error": "Failed to create article"
            }), 500
    except Exception as e:
        logger.error(f"Error creating KB article: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/knowledge-base/<article_id>', methods=['PUT'])
@admin_required
def update_kb_article(article_id):
    """Update a KB article"""
    try:
        data = request.json
        article = db.update_kb_article(article_id, **data)
        
        # Also update in ChromaDB
        if article:
            kb.update_entry(
                entry_id=article_id,
                issue=data.get('title'),
                solution=data.get('solution'),
                source=data.get('source'),
                category=data.get('category'),
                subcategory=data.get('subcategory'),
                keywords=data.get('keywords')
            )
        
        if article:
            return jsonify({
                "success": True,
                "article": dict(article)
            })
        else:
            return jsonify({
                "success": False,
                "error": "Article not found"
            }), 404
    except Exception as e:
        logger.error(f"Error updating KB article: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/knowledge-base/<article_id>', methods=['DELETE'])
@admin_required
def delete_kb_article(article_id):
    """Delete a KB article"""
    try:
        db.delete_kb_article(article_id)
        kb.delete_entry(article_id)
        return jsonify({
            "success": True,
            "message": "Article deleted"
        })
    except Exception as e:
        logger.error(f"Error deleting KB article: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/knowledge-base/<article_id>/feedback', methods=['POST'])
@token_required
def kb_article_feedback(article_id):
    """Submit feedback for a KB article"""
    try:
        data = request.json
        helpful = data.get('helpful', True)
        db.update_kb_helpful(article_id, helpful)
        return jsonify({
            "success": True,
            "message": "Feedback recorded"
        })
    except Exception as e:
        logger.error(f"Error recording feedback: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/kb/search', methods=['POST'])
@token_required
def search_kb():
    """Search knowledge base"""
    try:
        data = request.json
        query = data.get('query')
        top_k = data.get('top_k', 3)
        if not query:
            return jsonify({
                "success": False,
                "error": "query is required"
            }), 400
        
        results = kb.search(query, top_k)
        
        return jsonify({
            "success": True,
            "results": results
        })
    except Exception as e:
        logger.error(f"Error searching KB: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/kb/stats', methods=['GET'])
@token_required
def kb_stats():
    """Get knowledge base statistics"""
    try:
        stats = kb.get_stats()
        return jsonify({
            "success": True,
            "stats": stats
        })
    except Exception as e:
        logger.error(f"Error getting KB stats: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==========================================
# AUDIT LOG ENDPOINTS
# ==========================================

@app.route('/api/audit-logs', methods=['GET'])
@admin_required
def get_audit_logs():
    """Get audit logs"""
    try:
        ticket_id = request.args.get('ticket_id')
        limit = request.args.get('limit', 100, type=int)
        
        logs = db.get_audit_logs(ticket_id=ticket_id, limit=limit)
        return jsonify({
            "success": True,
            "logs": [dict(l) for l in logs] if logs else []
        })
    except Exception as e:
        logger.error(f"Error getting audit logs: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==========================================
# NOTIFICATION SETTINGS ENDPOINTS
# ==========================================

@app.route('/api/notifications/settings', methods=['GET'])
@admin_required
def get_notification_settings():
    """Get notification settings"""
    try:
        settings = db.get_notification_settings()
        return jsonify({
            "success": True,
            "settings": dict(settings) if settings else {}
        })
    except Exception as e:
        logger.error(f"Error getting notification settings: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/notifications/settings', methods=['PUT'])
@admin_required
def update_notification_settings():
    """Update notification settings"""
    try:
        data = request.json
        settings = db.update_notification_settings(**data)
        if settings:
            return jsonify({
                "success": True,
                "settings": dict(settings)
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to update settings"
            }), 500
    except Exception as e:
        logger.error(f"Error updating notification settings: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==========================================
# ANALYTICS ENDPOINTS
# ==========================================

@app.route('/api/analytics/tickets', methods=['GET'])
@token_required
def get_ticket_analytics():
    """Get ticket statistics with real-time data and trends"""
    try:
        # First, sync SLA breach flags so the DB column stays up to date
        db.check_and_update_sla_breaches()
        
        stats = db.get_ticket_stats()
        by_category = db.get_tickets_by_category()
        by_priority = db.get_tickets_by_priority()
        active_techs = db.get_active_technician_count()
        avg_resolution = db.get_avg_resolution_time()
        trends = db.get_ticket_trends()
        
        stats_dict = dict(stats) if stats else {}
        stats_dict['active_technicians'] = active_techs
        stats_dict['avg_resolution_time'] = avg_resolution
        stats_dict.update(trends)
        
        return jsonify({
            "success": True,
            "stats": stats_dict,
            "by_category": [dict(c) for c in by_category] if by_category else [],
            "by_priority": [dict(p) for p in by_priority] if by_priority else []
        })
    except Exception as e:
        logger.error(f"Error getting ticket analytics: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/analytics/trend', methods=['GET'])
@token_required
def get_ticket_trend():
    """Get ticket trend over time"""
    try:
        days = request.args.get('days', 7, type=int)
        trend = db.get_recent_ticket_trend(days)
        return jsonify({
            "success": True,
            "trend": [dict(t) for t in trend] if trend else []
        })
    except Exception as e:
        logger.error(f"Error getting ticket trend: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/analytics/workload', methods=['GET'])
@token_required
def get_technician_workload():
    """Get technician workload distribution"""
    try:
        workload = db.get_technician_workload()
        return jsonify({
            "success": True,
            "workload": [dict(w) for w in workload] if workload else []
        })
    except Exception as e:
        logger.error(f"Error getting workload: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/analytics/sla', methods=['GET'])
@token_required
def get_sla_analytics():
    """Get SLA compliance analytics"""
    try:
        db.check_and_update_sla_breaches()
        sla = db.get_sla_compliance_stats()
        return jsonify({
            "success": True,
            "sla": dict(sla) if sla else {}
        })
    except Exception as e:
        logger.error(f"Error getting SLA analytics: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/analytics/resolution-time', methods=['GET'])
@token_required
def get_resolution_time_analytics():
    """Get resolution time distribution"""
    try:
        distribution = db.get_resolution_time_distribution()
        return jsonify({
            "success": True,
            "distribution": [dict(d) for d in distribution] if distribution else []
        })
    except Exception as e:
        logger.error(f"Error getting resolution time analytics: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/analytics/status', methods=['GET'])
@token_required
def get_status_analytics():
    """Get ticket status breakdown"""
    try:
        db.check_and_update_sla_breaches()
        statuses = db.get_tickets_by_status()
        return jsonify({
            "success": True,
            "statuses": [dict(s) for s in statuses] if statuses else []
        })
    except Exception as e:
        logger.error(f"Error getting status analytics: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/analytics/resolution-trend', methods=['GET'])
@token_required
def get_resolution_trend():
    """Get daily resolution trend"""
    try:
        days = request.args.get('days', 30, type=int)
        trend = db.get_daily_resolution_trend(days)
        return jsonify({
            "success": True,
            "trend": [dict(t) for t in trend] if trend else []
        })
    except Exception as e:
        logger.error(f"Error getting resolution trend: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/technicians/real-stats', methods=['GET'])
@token_required
def get_technician_real_stats():
    """Get real-time technician stats from tickets table"""
    try:
        stats = db.get_technician_real_stats()
        return jsonify({
            "success": True,
            "stats": [dict(s) for s in stats] if stats else []
        })
    except Exception as e:
        logger.error(f"Error getting technician real stats: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ==========================================
# KB CATEGORIES ENDPOINT
# ==========================================

@app.route('/api/kb/categories', methods=['GET'])
@token_required
def get_kb_categories():
    """Get KB categories"""
    try:
        categories = db.get_kb_categories()
        return jsonify({
            "success": True,
            "categories": [dict(c) for c in categories] if categories else []
        })
    except Exception as e:
        logger.error(f"Error getting KB categories: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


def initialize_app():
    """Initialize the application"""
    try:
        logger.info("Initializing IT Support System...")
        
        # Create sessions directory if it doesn't exist
        os.makedirs('sessions', exist_ok=True)
        
        # Initialize database schema
        logger.info("Initializing PostgreSQL database...")
        db.initialize_schema()
        
        # Knowledge base is auto-initialized in kb_chroma.py
        logger.info("Knowledge base initialized")
        
        logger.info("Application initialized successfully!")
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise


if __name__ == '__main__':
    # Initialize application
    initialize_app()
    
    # Run Flask app
    logger.info(f"Starting Flask server on port {config.FLASK_PORT}...")
    app.run(
        host='0.0.0.0',
        port=config.FLASK_PORT,
        debug=config.FLASK_DEBUG
    )