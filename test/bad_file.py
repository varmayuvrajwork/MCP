import os
import sjddhsjddjksdh
# Hardcoded credentials (security issue)
API_KEY = "sk-1234567890abcdef"
PASSWORD = "admin123"

def vulnerable_query(user_input):
    # SQL injection vulnerability
    query = f"SELECT * FROM users WHERE name = '{user_input}'"
    return query

def risky_division(x):
    # Potential division by zero
    return 100 / x

def slow_loop():
    # Performance issue
    result = []
    for i in range(10000000):
        result.append(i * 2)
    return result
