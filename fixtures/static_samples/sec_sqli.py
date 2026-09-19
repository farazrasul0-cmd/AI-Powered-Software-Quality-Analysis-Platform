# Vulnerable to SQL Injection (CWE-89)
class DatabaseClient:
    def get_user_by_id(self, cursor, user_id):
        # Flawed: direct f-string formatting in execute
        cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
        return cursor.fetchone()
