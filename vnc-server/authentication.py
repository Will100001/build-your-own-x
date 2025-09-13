#!/usr/bin/env python3
"""
Authentication Module for VNC Server
Provides simple username/password authentication.
"""

import hashlib
import hmac
import json
import os
import time
from typing import Dict, Optional, Callable
from dataclasses import dataclass


@dataclass
class User:
    """User account information."""
    username: str
    password_hash: str
    salt: str
    created_at: float
    last_login: Optional[float] = None
    login_attempts: int = 0


class VNCAuth:
    """VNC Authentication system."""
    
    def __init__(self, auth_file: str = "vnc_users.json"):
        self.auth_file = auth_file
        self.users: Dict[str, User] = {}
        self.max_login_attempts = 3
        self.lockout_duration = 300  # 5 minutes
        self.load_users()
        
    def _hash_password(self, password: str, salt: str) -> str:
        """Hash a password with salt using PBKDF2."""
        return hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000   # iterations
        ).hex()
    
    def _generate_salt(self) -> str:
        """Generate a random salt."""
        return hashlib.sha256(str(time.time()).encode()).hexdigest()[:16]
    
    def add_user(self, username: str, password: str) -> bool:
        """Add a new user account."""
        if username in self.users:
            return False  # User already exists
        
        salt = self._generate_salt()
        password_hash = self._hash_password(password, salt)
        
        user = User(
            username=username,
            password_hash=password_hash,
            salt=salt,
            created_at=time.time()
        )
        
        self.users[username] = user
        self.save_users()
        return True
    
    def remove_user(self, username: str) -> bool:
        """Remove a user account."""
        if username not in self.users:
            return False
        
        del self.users[username]
        self.save_users()
        return True
    
    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """Change a user's password."""
        if username not in self.users:
            return False
        
        user = self.users[username]
        old_hash = self._hash_password(old_password, user.salt)
        
        if not hmac.compare_digest(old_hash, user.password_hash):
            return False
        
        # Generate new salt and hash for new password
        new_salt = self._generate_salt()
        new_hash = self._hash_password(new_password, new_salt)
        
        user.password_hash = new_hash
        user.salt = new_salt
        
        self.save_users()
        return True
    
    def authenticate(self, username: str, password: str) -> bool:
        """Authenticate a user."""
        if username not in self.users:
            return False
        
        user = self.users[username]
        
        # Check if user is locked out
        if user.login_attempts >= self.max_login_attempts:
            if user.last_login and (time.time() - user.last_login) < self.lockout_duration:
                return False
            else:
                # Reset login attempts after lockout period
                user.login_attempts = 0
        
        # Verify password
        password_hash = self._hash_password(password, user.salt)
        
        if hmac.compare_digest(password_hash, user.password_hash):
            # Successful authentication
            user.last_login = time.time()
            user.login_attempts = 0
            self.save_users()
            return True
        else:
            # Failed authentication
            user.login_attempts += 1
            if user.login_attempts == 1:
                user.last_login = time.time()  # Record first failed attempt time
            self.save_users()
            return False
    
    def vnc_challenge_response(self, username: str, password: str, 
                              challenge: bytes) -> bytes:
        """Generate VNC authentication response."""
        # Simplified VNC authentication
        # In practice, this would use proper DES encryption
        
        key = (password + '\x00' * 8)[:8].encode('utf-8')
        response = bytearray()
        
        for i in range(16):
            response.append(challenge[i] ^ key[i % 8])
        
        return bytes(response)
    
    def create_auth_callback(self) -> Callable[[bytes, bytes], bool]:
        """Create an authentication callback for VNC protocol."""
        def auth_callback(challenge: bytes, response: bytes) -> bool:
            # For demo purposes, we'll use a simplified approach
            # In practice, you'd need to associate the challenge with a user
            
            # Check if default user exists and authenticate
            if 'admin' in self.users:
                expected_response = self.vnc_challenge_response('admin', 'password', challenge)
                return hmac.compare_digest(response, expected_response)
            
            return False
        
        return auth_callback
    
    def list_users(self) -> Dict[str, Dict]:
        """List all users (without sensitive information)."""
        user_list = {}
        for username, user in self.users.items():
            user_list[username] = {
                'created_at': user.created_at,
                'last_login': user.last_login,
                'login_attempts': user.login_attempts
            }
        return user_list
    
    def load_users(self):
        """Load users from file."""
        if not os.path.exists(self.auth_file):
            # Create default admin user
            self.add_user('admin', 'password')
            return
        
        try:
            with open(self.auth_file, 'r') as f:
                data = json.load(f)
            
            self.users = {}
            for username, user_data in data.items():
                user = User(
                    username=username,
                    password_hash=user_data['password_hash'],
                    salt=user_data['salt'],
                    created_at=user_data['created_at'],
                    last_login=user_data.get('last_login'),
                    login_attempts=user_data.get('login_attempts', 0)
                )
                self.users[username] = user
                
        except (json.JSONDecodeError, KeyError, FileNotFoundError):
            # If file is corrupted, create default user
            self.users = {}
            self.add_user('admin', 'password')
    
    def save_users(self):
        """Save users to file."""
        data = {}
        for username, user in self.users.items():
            data[username] = {
                'password_hash': user.password_hash,
                'salt': user.salt,
                'created_at': user.created_at,
                'last_login': user.last_login,
                'login_attempts': user.login_attempts
            }
        
        try:
            with open(self.auth_file, 'w') as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            print(f"Error saving users: {e}")


class SimpleAuth:
    """Simple authentication without persistence."""
    
    def __init__(self):
        self.credentials = {
            'admin': 'password',
            'user': 'user123'
        }
    
    def authenticate(self, username: str, password: str) -> bool:
        """Simple authentication check."""
        return self.credentials.get(username) == password
    
    def add_user(self, username: str, password: str):
        """Add a user."""
        self.credentials[username] = password
    
    def remove_user(self, username: str):
        """Remove a user."""
        if username in self.credentials:
            del self.credentials[username]
    
    def list_users(self):
        """List usernames."""
        return list(self.credentials.keys())
    
    def create_auth_callback(self) -> Callable[[bytes, bytes], bool]:
        """Create a simple authentication callback."""
        def auth_callback(challenge: bytes, response: bytes) -> bool:
            # Simplified: check if response matches expected pattern
            # This is a demo implementation
            expected = bytearray()
            admin_password = 'password'.encode('utf-8')
            
            for i in range(16):
                expected.append(challenge[i] ^ admin_password[i % len(admin_password)])
            
            return hmac.compare_digest(response, bytes(expected))
        
        return auth_callback


if __name__ == "__main__":
    # Test authentication system
    print("Testing VNC Authentication System")
    
    # Test VNCAuth
    auth = VNCAuth("test_users.json")
    
    print(f"Users: {list(auth.users.keys())}")
    
    # Test authentication
    print(f"Admin auth (correct): {auth.authenticate('admin', 'password')}")
    print(f"Admin auth (wrong): {auth.authenticate('admin', 'wrong')}")
    
    # Add new user
    auth.add_user('testuser', 'testpass')
    print(f"Added testuser: {auth.authenticate('testuser', 'testpass')}")
    
    # Test lockout
    print("Testing lockout mechanism...")
    for i in range(4):
        result = auth.authenticate('testuser', 'wrong')
        print(f"Attempt {i+1}: {result}")
    
    # Clean up test file
    if os.path.exists("test_users.json"):
        os.remove("test_users.json")
    
    print("\nTesting Simple Authentication")
    simple_auth = SimpleAuth()
    print(f"Users: {simple_auth.list_users()}")
    print(f"Admin auth: {simple_auth.authenticate('admin', 'password')}")
    
    # Test auth callback
    callback = simple_auth.create_auth_callback()
    test_challenge = b'1234567890123456'
    test_response = callback.__code__.co_varnames  # This is just for demo
    print("Auth callback created successfully")