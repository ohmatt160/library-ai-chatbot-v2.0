"""
SQL Migration script to add columns for OpenLibrary reservations.
Run this script to update your database schema.
"""

# For MySQL, run these SQL commands:
"""
ALTER TABLE reserve_requests 
ADD COLUMN notes TEXT AFTER expiry_date;

ALTER TABLE reserve_requests 
MODIFY COLUMN status ENUM('active', 'fulfilled', 'cancelled', 'expired', 'pending_ill') DEFAULT 'active';
"""

# For SQLite (development), run:
"""
ALTER TABLE reserve_requests ADD COLUMN notes TEXT;
"""

print("""
To add the needed columns to your database, run the following SQL:

=== For MySQL (Production) ===
ALTER TABLE reserve_requests ADD COLUMN notes TEXT AFTER expiry_date;
ALTER TABLE reserve_requests MODIFY COLUMN status ENUM('active', 'fulfilled', 'cancelled', 'expired', 'pending_ill') DEFAULT 'active';

=== For SQLite (Development) ===
ALTER TABLE reserve_requests ADD COLUMN notes TEXT;

After running the SQL, restart your application.
""")
