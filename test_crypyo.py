import unittest
import sys
import os
import json
import base64
import hashlib
import tempfile
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from Crypto.PublicKey import RSA
    from Crypto.Cipher import AES, PKCS1_OAEP
    from Crypto.Hash import SHA256
    from Crypto.Signature import pkcs1_15
    from Crypto.Random import get_random_bytes
except ImportError as e:
    print(f"❌ Crypto library import error: {e}")
    print("Please install pycryptodome: pip install pycryptodome")
    sys.exit(1)

try:
    from stegno_gui import CertificateAuthority, DocumentSigner
except ImportError as e:
    print(f"❌ Application import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


class TestCertificateAuthority(unittest.TestCase):
    """Test Certificate Authority functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once before all tests"""
        print("\n🔐 Testing Certificate Authority...")
    
    def setUp(self):
        """Set up before each test"""
        self.ca = CertificateAuthority()
        self.ca.initialize()
        
        # Generate test key pair
        self.key = RSA.generate(2048)
        self.public_key = self.key.publickey().export_key().decode('utf-8')
        self.private_key = self.key.export_key().decode('utf-8')
    
    def test_ca_initialization(self):
        """Test CA initialization creates valid self-signed certificate"""
        self.assertIsNotNone(self.ca.ca_cert, "CA certificate should not be None")
        self.assertIsNotNone(self.ca.ca_key, "CA key should not be None")
        
        # FIXED: Match the actual CA name from your code
        expected_ca_name = 'Secure Steganography CA'
        self.assertEqual(self.ca.ca_cert['subject']['CN'], expected_ca_name, 
                        f"CA certificate subject should be '{expected_ca_name}'")
        
        self.assertTrue(self.ca.ca_cert['is_ca'], "CA certificate should be marked as CA")
        
        # Check that the CA has the right structure
        self.assertIn('version', self.ca.ca_cert)
        self.assertIn('serial', self.ca.ca_cert)
        self.assertIn('issuer', self.ca.ca_cert)
        self.assertIn('validity', self.ca.ca_cert)
        self.assertIn('public_key', self.ca.ca_cert)
        
        print("  ✅ CA initialization test passed")
    
    def test_certificate_issuance(self):
        """Test issuing a certificate to a user"""
        user_info = {
            'username': 'testuser',
            'email': 'test@example.com',
            'organization': 'Test Organization'
        }
        
        cert = self.ca.issue_certificate(1, self.public_key, user_info)
        
        self.assertEqual(cert['serial'], 'USR-0001', "Certificate serial should be USR-0001")
        self.assertEqual(cert['subject']['CN'], 'testuser', "Certificate common name should match username")
        self.assertEqual(cert['subject']['email'], 'test@example.com', "Email should match")
        self.assertEqual(cert['subject']['O'], 'Test Organization', "Organization should match")
        self.assertIn('signature', cert, "Certificate should have a signature")
        self.assertIsNotNone(cert['public_key'], "Public key should be present")
        
        # Check that issuer is the CA
        self.assertEqual(cert['issuer']['CN'], 'Secure Steganography CA', 
                        "Issuer should be the CA")
        
        # Check validity dates
        not_before = cert['validity']['not_before']
        not_after = cert['validity']['not_after']
        if isinstance(not_before, str):
            not_before = datetime.fromisoformat(not_before)
        if isinstance(not_after, str):
            not_after = datetime.fromisoformat(not_after)
        
        self.assertLess(not_before, not_after, "Not before should be before not after")
        self.assertGreater(not_after, datetime.now(), "Certificate should be valid now")
        
        print("  ✅ Certificate issuance test passed")
    
    def test_certificate_verification(self):
        """Test verifying a valid certificate"""
        user_info = {
            'username': 'testuser',
            'email': 'test@example.com'
        }
        
        cert = self.ca.issue_certificate(1, self.public_key, user_info)
        valid, message = self.ca.verify_certificate(1, cert)
        
        self.assertTrue(valid, "Certificate should be valid")
        self.assertEqual(message, "Certificate valid", "Verification message should indicate valid")
        print("  ✅ Certificate verification test passed")
    
    def test_certificate_revocation(self):
        """Test certificate revocation"""
        user_info = {
            'username': 'testuser',
            'email': 'test@example.com'
        }
        
        cert = self.ca.issue_certificate(1, self.public_key, user_info)
        
        # Verify before revocation
        valid_before, _ = self.ca.verify_certificate(1, cert)
        self.assertTrue(valid_before, "Certificate should be valid before revocation")
        
        # Revoke certificate
        result = self.ca.revoke_certificate(1)
        self.assertTrue(result, "Revocation should succeed")
        
        # Verify after revocation
        valid_after, message = self.ca.verify_certificate(1, cert)
        self.assertFalse(valid_after, "Certificate should be invalid after revocation")
        self.assertEqual(message, "Certificate revoked", "Should indicate revocation")
        
        print("  ✅ Certificate revocation test passed")
    
    def test_invalid_certificate_verification(self):
        """Test verification of invalid certificate"""
        # Create a certificate for user 1
        user_info = {'username': 'user1', 'email': 'user1@example.com'}
        cert = self.ca.issue_certificate(1, self.public_key, user_info)
        
        # Try to verify with wrong user ID
        valid, message = self.ca.verify_certificate(2, cert)
        self.assertFalse(valid, "Should fail with wrong user ID")
        self.assertEqual(message, "Certificate not issued by this CA", 
                        "Should indicate certificate not found")
        
        print("  ✅ Invalid certificate test passed")
    
    def test_certificate_expiry(self):
        """Test certificate expiry detection"""
        # Create a certificate with custom expiry
        user_info = {'username': 'testuser', 'email': 'test@example.com'}
        cert = self.ca.issue_certificate(1, self.public_key, user_info)
        
        # Manually set expiry to past date
        past_date = datetime.now() - timedelta(days=400)
        cert['validity']['not_after'] = past_date.isoformat()
        
        # Override the stored certificate in CA
        self.ca.users_certificates[1] = cert
        
        # Verify - should detect expiry
        valid, message = self.ca.verify_certificate(1, cert)
        self.assertFalse(valid, "Expired certificate should be invalid")
        self.assertEqual(message, "Certificate expired", "Should indicate expiry")
        
        print("  ✅ Certificate expiry test passed")


class TestDocumentSigner(unittest.TestCase):
    """Test document signing and verification functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once before all tests"""
        print("\n📝 Testing Document Signer...")
    
    def setUp(self):
        """Set up before each test"""
        self.signer = DocumentSigner()
        
        # Generate key pair
        self.key = RSA.generate(2048)
        self.private_key = self.key.export_key().decode('utf-8')
        self.public_key = self.key.publickey().export_key().decode('utf-8')
        
        # Create a simple CA for certificate testing
        self.ca = CertificateAuthority()
        self.ca.initialize()
        
        # Test documents
        self.test_text = b"This is a test document for signing verification."
        self.test_binary = os.urandom(1024)  # 1KB random data
    
    def test_document_signing(self):
        """Test signing a document"""
        signed_package = self.signer.sign_document(self.test_text, self.private_key)
        
        self.assertIn('document', signed_package, "Package should contain document")
        self.assertIn('signature', signed_package, "Package should contain signature")
        self.assertIn('timestamp', signed_package, "Package should contain timestamp")
        self.assertIn('hash_algorithm', signed_package, "Package should specify hash algorithm")
        self.assertIn('signature_algorithm', signed_package, "Package should specify signature algorithm")
        
        # Verify we can decode the document
        decoded = base64.b64decode(signed_package['document'])
        self.assertEqual(decoded, self.test_text, "Decoded document should match original")
        
        print("  ✅ Document signing test passed")
    
    def test_signature_verification(self):
        """Test verifying a valid signature"""
        signed_package = self.signer.sign_document(self.test_text, self.private_key)
        
        result = self.signer.verify_signature(signed_package, self.public_key)
        
        self.assertTrue(result['verified'], "Signature should be verified")
        self.assertEqual(result['document'], self.test_text, "Extracted document should match")
        self.assertIn('timestamp', result, "Result should contain timestamp")
        
        print("  ✅ Signature verification test passed")
    
    def test_tampered_document(self):
        """Test detection of tampered document"""
        signed_package = self.signer.sign_document(self.test_text, self.private_key)
        
        # Tamper with the document
        tampered_text = b"This document has been tampered with!"
        signed_package['document'] = base64.b64encode(tampered_text).decode('utf-8')
        
        result = self.signer.verify_signature(signed_package, self.public_key)
        
        self.assertFalse(result['verified'], "Tampered document should fail verification")
        self.assertIsNone(result['document'], "Document should be None on failure")
        self.assertIn('error', result, "Result should contain error message")
        
        print("  ✅ Tampered document detection test passed")
    
    def test_tampered_signature(self):
        """Test detection of tampered signature"""
        signed_package = self.signer.sign_document(self.test_text, self.private_key)
        
        # Tamper with the signature
        signed_package['signature'] = base64.b64encode(b"fake_signature").decode('utf-8')
        
        result = self.signer.verify_signature(signed_package, self.public_key)
        
        self.assertFalse(result['verified'], "Tampered signature should fail verification")
        
        print("  ✅ Tampered signature detection test passed")
    
    def test_binary_document_signing(self):
        """Test signing binary data"""
        signed_package = self.signer.sign_document(self.test_binary, self.private_key)
        
        result = self.signer.verify_signature(signed_package, self.public_key)
        
        self.assertTrue(result['verified'], "Binary document signature should verify")
        self.assertEqual(result['document'], self.test_binary, "Binary data should match")
        
        print("  ✅ Binary document signing test passed")
    
    def test_certificate_verification(self):
        """Test verification with certificate"""
        # Create user certificate
        user_info = {
            'username': 'testuser',
            'email': 'test@example.com'
        }
        cert = self.ca.issue_certificate(1, self.public_key, user_info)
        
        signed_package = self.signer.sign_document(self.test_text, self.private_key)
        
        result = self.signer.verify_signature(signed_package, self.public_key, cert)
        
        self.assertTrue(result['verified'], "Signature should verify with certificate")
        self.assertEqual(result['signer'], 'testuser', "Should extract signer name from certificate")
        
        print("  ✅ Certificate verification test passed")
    
    def test_expired_certificate(self):
        """Test verification with expired certificate"""
        # Create an expired certificate
        cert = {
            'version': '1.0',
            'serial': 'USR-0001',
            'subject': {'CN': 'testuser', 'email': 'test@example.com'},
            'validity': {
                'not_before': (datetime.now() - timedelta(days=400)).isoformat(),
                'not_after': (datetime.now() - timedelta(days=35)).isoformat()
            }
        }
        
        signed_package = self.signer.sign_document(self.test_text, self.private_key)
        
        result = self.signer.verify_signature(signed_package, self.public_key, cert)
        
        self.assertFalse(result['verified'], "Should fail with expired certificate")
        self.assertEqual(result.get('error'), 'Certificate expired', 
                        "Should indicate certificate expired")
        
        print("  ✅ Expired certificate test passed")


class TestAESEncryption(unittest.TestCase):
    """Test AES encryption functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once before all tests"""
        print("\n🔒 Testing AES Encryption...")
    
    def test_aes_encryption_decryption(self):
        """Test AES encryption and decryption"""
        password = "testpassword123"
        data = b"Sensitive data that needs encryption"
        
        # Derive key using PBKDF2
        salt = b'salt'  # In production, use random salt
        kdf = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), 
                                 salt, 100000, dklen=32)
        
        # Encrypt
        cipher = AES.new(kdf, AES.MODE_GCM)
        ciphertext, tag = cipher.encrypt_and_digest(data)
        
        # Package for storage
        encrypted_package = {
            'ciphertext': base64.b64encode(ciphertext).decode('utf-8'),
            'tag': base64.b64encode(tag).decode('utf-8'),
            'nonce': base64.b64encode(cipher.nonce).decode('utf-8'),
            'salt': base64.b64encode(salt).decode('utf-8')
        }
        
        # Decrypt
        kdf2 = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), 
                                  base64.b64decode(encrypted_package['salt']), 
                                  100000, dklen=32)
        
        cipher2 = AES.new(kdf2, AES.MODE_GCM, 
                         nonce=base64.b64decode(encrypted_package['nonce']))
        
        decrypted = cipher2.decrypt_and_verify(
            base64.b64decode(encrypted_package['ciphertext']),
            base64.b64decode(encrypted_package['tag'])
        )
        
        self.assertEqual(decrypted, data, "Decrypted data should match original")
        
        print("  ✅ AES encryption/decryption test passed")
    
    def test_wrong_password(self):
        """Test decryption with wrong password"""
        correct_password = "correctpassword"
        wrong_password = "wrongpassword"
        data = b"Test data"
        
        # Encrypt with correct password
        salt = b'salt'
        kdf = hashlib.pbkdf2_hmac('sha256', correct_password.encode('utf-8'), 
                                 salt, 100000, dklen=32)
        cipher = AES.new(kdf, AES.MODE_GCM)
        ciphertext, tag = cipher.encrypt_and_digest(data)
        
        # Try to decrypt with wrong password
        kdf2 = hashlib.pbkdf2_hmac('sha256', wrong_password.encode('utf-8'), 
                                  salt, 100000, dklen=32)
        cipher2 = AES.new(kdf2, AES.MODE_GCM, nonce=cipher.nonce)
        
        with self.assertRaises(Exception):
            cipher2.decrypt_and_verify(ciphertext, tag)
        
        print("  ✅ Wrong password detection test passed")
    
    def test_data_integrity(self):
        """Test that tampered data is detected"""
        password = "testpassword"
        data = b"Important data"
        
        salt = b'salt'
        kdf = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), 
                                 salt, 100000, dklen=32)
        cipher = AES.new(kdf, AES.MODE_GCM)
        ciphertext, tag = cipher.encrypt_and_digest(data)
        
        # Tamper with ciphertext
        tampered = bytearray(ciphertext)
        tampered[10] ^= 0xFF  # Flip a bit
        
        cipher2 = AES.new(kdf, AES.MODE_GCM, nonce=cipher.nonce)
        
        with self.assertRaises(Exception):
            cipher2.decrypt_and_verify(bytes(tampered), tag)
        
        print("  ✅ Data integrity test passed")
    
    def test_different_salts(self):
        """Test that different salts produce different keys"""
        password = "testpassword"
        data = b"Test data"
        
        salt1 = b'salt1'
        salt2 = b'salt2'
        
        kdf1 = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), 
                                  salt1, 100000, dklen=32)
        kdf2 = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), 
                                  salt2, 100000, dklen=32)
        
        cipher1 = AES.new(kdf1, AES.MODE_GCM)
        ciphertext1, tag1 = cipher1.encrypt_and_digest(data)
        
        # Try to decrypt with different key
        cipher2 = AES.new(kdf2, AES.MODE_GCM, nonce=cipher1.nonce)
        
        with self.assertRaises(Exception):
            cipher2.decrypt_and_verify(ciphertext1, tag1)
        
        print("  ✅ Salt variation test passed")


class TestRSAEncryption(unittest.TestCase):
    """Test RSA encryption functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once before all tests"""
        print("\n🔑 Testing RSA Encryption...")
    
    def setUp(self):
        """Set up before each test"""
        self.key = RSA.generate(2048)
        self.public_key = self.key.publickey()
        self.private_key = self.key
    
    def test_rsa_encryption_decryption(self):
        """Test RSA encryption and decryption"""
        data = b"Secret message for RSA testing"
        
        # Encrypt with public key
        cipher = PKCS1_OAEP.new(self.public_key)
        encrypted = cipher.encrypt(data)
        
        # Decrypt with private key
        cipher = PKCS1_OAEP.new(self.private_key)
        decrypted = cipher.decrypt(encrypted)
        
        self.assertEqual(decrypted, data, "Decrypted data should match original")
        
        print("  ✅ RSA encryption/decryption test passed")
    
    def test_rsa_different_key_pairs(self):
        """Test that different key pairs don't work"""
        data = b"Test message"
        
        # Generate another key pair
        other_key = RSA.generate(2048)
        other_public = other_key.publickey()
        
        # Encrypt with our public key
        cipher = PKCS1_OAEP.new(self.public_key)
        encrypted = cipher.encrypt(data)
        
        # Try to decrypt with other private key
        other_cipher = PKCS1_OAEP.new(other_key)
        
        with self.assertRaises(Exception):
            other_cipher.decrypt(encrypted)
        
        print("  ✅ Key mismatch detection test passed")
    
    def test_rsa_key_sizes(self):
        """Test different RSA key sizes"""
        test_data = b"Small message"
        
        # Test with different key sizes
        key_sizes = [1024, 2048]  # 3072 might be slow
        
        for bits in key_sizes:
            key = RSA.generate(bits)
            public = key.publickey()
            private = key
            
            cipher_enc = PKCS1_OAEP.new(public)
            encrypted = cipher_enc.encrypt(test_data)
            
            cipher_dec = PKCS1_OAEP.new(private)
            decrypted = cipher_dec.decrypt(encrypted)
            
            self.assertEqual(decrypted, test_data, f"Failed for {bits}-bit key")
        
        print("  ✅ RSA key size test passed")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
