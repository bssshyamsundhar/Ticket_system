"""Fix user passwords"""
import bcrypt
import sys
sys.path.insert(0, '.')
from db.postgres import db

# Generate proper hash
password = 'user123'
pw_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Update all test users
users = ['john.doe@company.com', 'jane.smith@company.com', 'mike.wilson@company.com', 'sarah.johnson@company.com']
for email in users:
    db.execute_query("UPDATE users SET password_hash = %s WHERE email = %s", (pw_hash, email))
    print(f"Updated password for {email}")

# Also fix admin
admin_hash = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
db.execute_query("UPDATE users SET password_hash = %s WHERE email = %s", (admin_hash, 'admin@company.com'))
print("Updated password for admin@company.com")

print("\nAll passwords updated!")
