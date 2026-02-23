import unittest
import sys
import os
import tempfile
import json
import hashlib
import base64
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from Crypto.PublicKey import RSA
    from Crypto.Cipher import AES
except ImportError as e:
    print(f"❌ Crypto library import error: {e}")
    sys.exit(1)

try:
    from PIL import Image
except ImportError as e:
    print(f"❌ PIL import error: {e}")
    sys.exit(1)

try:
    from stegno_gui import (
        CertificateAuthority, DocumentSigner, AdvancedSteganography,
        FileHandler, SecurityAuditor
    )
except ImportError as e:
    print(f"❌ Application import error: {e}")
    sys.exit(1)


class TestIntegration(unittest.TestCase):
    """Integration tests combining multiple SecurePixel components"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once before all tests"""
        print("\n🔄 Running Integration Tests...")
    
    def setUp(self):
        """Set up before each test"""
        # Initialize components
        self.ca = CertificateAuthority()
        self.ca.initialize()
        self.signer = DocumentSigner()
        self.stego = AdvancedSteganography()
        self.file_handler = FileHandler()
        self.auditor = SecurityAuditor()
        
        # Create temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
        # Create test image
        self.test_image = os.path.join(self.test_dir, 'cover.png')
        img = Image.new('RGB', (200, 200), color='white')
        img.save(self.test_image)
        
        # Create test document
        self.test_doc = os.path.join(self.test_dir, 'test.txt')
        with open(self.test_doc, 'w') as f:
            f.write("This is a test document for integration testing.\n")
            f.write("It contains multiple lines of text.\n")
            f.write("This will be signed and hidden in an image.")
        
        # Generate test keys
        self.test_key = RSA.generate(2048)
        self.private_key = self.test_key.export_key().decode('utf-8')
        self.public_key = self.test_key.publickey().export_key().decode('utf-8')
        
        # Create test user certificate
        user_info = {
            'username': 'testuser',
            'email': 'test@example.com',
            'organization': 'Test Organization'
        }
        self.certificate = self.ca.issue_certificate(1, self.public_key, user_info)
    
    def tearDown(self):
        """Clean up test files"""
        import shutil
        shutil.rmtree(self.test_dir)
    
    def test_full_document_workflow(self):
        """Test complete document signing and verification workflow"""
        print("\n  📄 Testing full document workflow...")
        
        # 1. Read document
        with open(self.test_doc, 'rb') as f:
            doc_data = f.read()
        original_hash = hashlib.sha256(doc_data).hexdigest()
        
        # 2. Sign document
        signed_package = self.signer.sign_document(doc_data, self.private_key)
        
        # 3. Verify signature immediately
        result = self.signer.verify_signature(signed_package, self.public_key, self.certificate)
        
        self.assertTrue(result['verified'], "Signature should verify immediately")
        self.assertEqual(result['signer'], 'testuser', "Signer name should match")
        self.assertEqual(result['document'], doc_data, "Extracted document should match")
        
        # 4. Save signed package
        signed_file = os.path.join(self.test_dir, 'signed.json')
        with open(signed_file, 'w') as f:
            json.dump(signed_package, f, indent=2)
        
        # 5. Load and verify again
        with open(signed_file, 'r') as f:
            loaded_package = json.load(f)
        
        result2 = self.signer.verify_signature(loaded_package, self.public_key, self.certificate)
        
        self.assertTrue(result2['verified'], "Signature should verify after save/load")
        self.assertEqual(hashlib.sha256(result2['document']).hexdigest(), original_hash, 
                        "Document hash should match")
        
        print("  ✅ Full document workflow test passed")
    
    def test_steganography_with_document(self):
        """Test hiding signed document in image"""
        print("\n  🖼️ Testing steganography with document...")
        
        # 1. Read and sign document
        with open(self.test_doc, 'rb') as f:
            doc_data = f.read()
        
        signed_package = self.signer.sign_document(doc_data, self.private_key)
        package_json = json.dumps(signed_package).encode('utf-8')
        
        # 2. Hide in image
        stego_image = os.path.join(self.test_dir, 'stego.png')
        success, message = self.stego.embed_data_lsb(
            self.test_image,
            package_json,
            stego_image
        )
        
        self.assertTrue(success, f"Steganography embedding failed: {message}")
        self.assertTrue(os.path.exists(stego_image), "Stego image not created")
        
        # 3. Extract from image
        extracted_data, metadata = self.stego.extract_data_lsb(stego_image)
        self.assertIsNotNone(extracted_data, "No data extracted from stego image")
        
        extracted_package = json.loads(extracted_data.decode('utf-8'))
        
        # 4. Verify extracted signature
        result = self.signer.verify_signature(extracted_package, self.public_key, self.certificate)
        
        self.assertTrue(result['verified'], "Extracted signature should verify")
        self.assertEqual(result['document'], doc_data, "Extracted document should match")
        self.assertIn('timestamp', metadata, "Metadata should contain timestamp")
        self.assertEqual(metadata['method'], 'LSB', "Metadata should indicate LSB method")
        
        print("  ✅ Steganography with document test passed")
    
    def test_encrypted_steganography(self):
        """Test encrypted data hidden in image"""
        print("\n  🔒 Testing encrypted steganography...")
        
        # 1. Create encrypted data
        password = "StrongPassword123!"
        data = b"Secret message that needs encryption before hiding"
        
        # Derive key
        salt = b'secure_salt'
        kdf = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), 
                                 salt, 100000, dklen=32)
        
        # Encrypt
        cipher = AES.new(kdf, AES.MODE_GCM)
        ciphertext, tag = cipher.encrypt_and_digest(data)
        
        # Package encrypted data (nonce + tag + ciphertext)
        encrypted_package = cipher.nonce + tag + ciphertext
        
        # 2. Hide encrypted data in image
        stego_image = os.path.join(self.test_dir, 'encrypted_stego.png')
        success, message = self.stego.embed_data_lsb(
            self.test_image,
            encrypted_package,
            stego_image
        )
        
        self.assertTrue(success, f"Embedding encrypted data failed: {message}")
        
        # 3. Extract from image
        extracted_encrypted, metadata = self.stego.extract_data_lsb(stego_image)
        
        # 4. Decrypt
        nonce = extracted_encrypted[:16]
        tag = extracted_encrypted[16:32]
        ciphertext = extracted_encrypted[32:]
        
        kdf2 = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), 
                                  salt, 100000, dklen=32)
        cipher2 = AES.new(kdf2, AES.MODE_GCM, nonce=nonce)
        decrypted = cipher2.decrypt_and_verify(ciphertext, tag)
        
        self.assertEqual(decrypted, data, "Decrypted data should match original")
        
        print("  ✅ Encrypted steganography test passed")
    
    def test_message_with_attachment(self):
        """Test secure message with file attachment"""
        print("\n  📎 Testing secure message with attachment...")
        
        # Create message with attachment
        message = {
            'sender': 'alice',
            'recipient': 'bob',
            'subject': 'Secret Project Files',
            'message': 'Here are the files you requested.',
            'timestamp': datetime.now().isoformat(),
            'attachment': {
                'name': 'project_plan.pdf',
                'data': base64.b64encode(b"Fake PDF content").decode('utf-8'),
                'size': 1024,
                'type': 'PDF'
            }
        }
        
        # Convert to JSON
        message_json = json.dumps(message).encode('utf-8')
        
        # Hide in image
        stego_image = os.path.join(self.test_dir, 'message_stego.png')
        success, _ = self.stego.embed_data_lsb(
            self.test_image,
            message_json,
            stego_image
        )
        
        self.assertTrue(success)
        
        # Extract and parse
        extracted_data, _ = self.stego.extract_data_lsb(stego_image)
        extracted_message = json.loads(extracted_data.decode('utf-8'))
        
        # Verify attachment
        self.assertEqual(extracted_message['subject'], 'Secret Project Files')
        self.assertIn('attachment', extracted_message)
        self.assertEqual(extracted_message['attachment']['name'], 'project_plan.pdf')
        
        # Decode attachment
        attachment_data = base64.b64decode(extracted_message['attachment']['data'])
        self.assertEqual(attachment_data, b"Fake PDF content")
        
        print("  ✅ Message with attachment test passed")
    
    def test_file_handler_detection(self):
        """Test file handler type detection"""
        print("\n  📁 Testing file handler detection...")
        
        # Test text file
        with open(self.test_doc, 'rb') as f:
            text_data = f.read()
        
        text_info = self.file_handler.get_file_info(text_data, 'test.txt')
        self.assertTrue(text_info['is_text'], "Should detect text file")
        self.assertFalse(text_info['is_image'], "Should not detect as image")
        self.assertEqual(text_info['extension'], '.txt')
        self.assertIsNotNone(text_info['preview'], "Should generate preview")
        
        # Test image file
        with open(self.test_image, 'rb') as f:
            image_data = f.read()
        
        image_info = self.file_handler.get_file_info(image_data, 'test.png')
        self.assertTrue(image_info['is_image'], "Should detect image file")
        self.assertFalse(image_info['is_text'], "Should not detect as text")
        self.assertEqual(image_info['extension'], '.png')
        
        # Test binary detection
        binary_data = os.urandom(100)
        binary_info = self.file_handler.get_file_info(binary_data)
        self.assertFalse(binary_info['is_text'], "Binary shouldn't be text")
        self.assertFalse(binary_info['is_image'], "Binary shouldn't be image")
        
        print("  ✅ File handler detection test passed")
    
    def test_certificate_lifecycle(self):
        """Test complete certificate lifecycle"""
        print("\n  🎫 Testing certificate lifecycle...")
        
        # 1. Issue certificate
        user_info = {
            'username': 'newuser',
            'email': 'new@example.com',
            'organization': 'New Org'
        }
        cert = self.ca.issue_certificate(2, self.public_key, user_info)
        
        self.assertEqual(cert['serial'], 'USR-0002')
        self.assertEqual(cert['subject']['CN'], 'newuser')
        self.assertIn('signature', cert)
        
        # 2. Verify certificate
        valid, message = self.ca.verify_certificate(2, cert)
        self.assertTrue(valid)
        self.assertEqual(message, "Certificate valid")
        
        # 3. Revoke certificate
        revoked = self.ca.revoke_certificate(2)
        self.assertTrue(revoked)
        
        # 4. Verify revocation
        valid, message = self.ca.verify_certificate(2, cert)
        self.assertFalse(valid)
        self.assertEqual(message, "Certificate revoked")
        
        # 5. Check user not in revoked list
        self.assertIn(2, self.ca.revoked_certificates)
        
        print("  ✅ Certificate lifecycle test passed")
    
    def test_security_audit(self):
        """Test security audit functionality"""
        print("\n  🔍 Testing security audit...")
        
        results = self.auditor.run_all_tests()
        
        # Check all expected tests are present
        expected_tests = [
            'certificate_validation',
            'key_strength', 
            'encryption_parameters',
            'steganography_security'
        ]
        
        for test_name in expected_tests:
            self.assertIn(test_name, results, f"Missing test: {test_name}")
        
        # Check test results structure
        for test_name, result in results.items():
            self.assertIn('test', result, f"Missing 'test' field in {test_name}")
            self.assertIn('passed', result, f"Missing 'passed' field in {test_name}")
            self.assertIn('details', result, f"Missing 'details' field in {test_name}")
            self.assertIsInstance(result['passed'], bool, f"'passed' should be boolean in {test_name}")
        
        print("  ✅ Security audit test passed")
    
    def test_end_to_end_workflow(self):
        """Complete end-to-end workflow"""
        print("\n  🔄 Testing end-to-end workflow...")
        
        # Step 1: User creates document
        document_content = b"Confidential: Project X Launch Date: 2024-12-01"
        
        # Step 2: User signs document
        signed_package = self.signer.sign_document(document_content, self.private_key)
        
        # Step 3: User hides signed document in image
        stego_image = os.path.join(self.test_dir, 'final_stego.png')
        self.stego.embed_data_lsb(
            self.test_image,
            json.dumps(signed_package).encode('utf-8'),
            stego_image
        )
        
        # Step 4: Recipient extracts from image
        extracted_data, _ = self.stego.extract_data_lsb(stego_image)
        extracted_package = json.loads(extracted_data.decode('utf-8'))
        
        # Step 5: Recipient verifies signature
        verification = self.signer.verify_signature(
            extracted_package, 
            self.public_key, 
            self.certificate
        )
        
        # Step 6: Verify everything worked
        self.assertTrue(verification['verified'], "Signature verification failed")
        self.assertEqual(verification['document'], document_content, 
                        "Document content mismatch")
        self.assertEqual(verification['signer'], 'testuser', 
                        "Signer name mismatch")
        
        print("  ✅ End-to-end workflow test passed")
    
    def test_error_handling(self):
        """Test error handling in combined workflows"""
        print("\n  ⚠️ Testing error handling...")
        
        # Test 1: Tamper with stego image
        document = b"Important document"
        signed = self.signer.sign_document(document, self.private_key)
        
        stego_image = os.path.join(self.test_dir, 'error_test.png')
        self.stego.embed_data_lsb(
            self.test_image,
            json.dumps(signed).encode('utf-8'),
            stego_image
        )
        
        # Tamper with the image (save as JPEG - lossy compression)
        img = Image.open(stego_image)
        jpeg_path = os.path.join(self.test_dir, 'tampered.jpg')
        img.save(jpeg_path, 'JPEG', quality=50)
        
        # Try to extract - should fail or return wrong data
        extracted, _ = self.stego.extract_data_lsb(jpeg_path)
        
        # Test 2: Wrong certificate
        wrong_key = RSA.generate(2048)
        wrong_public = wrong_key.publickey().export_key().decode('utf-8')
        
        verification = self.signer.verify_signature(signed, wrong_public)
        self.assertFalse(verification['verified'], 
                        "Should fail with wrong public key")
        
        # Test 3: Missing data
        empty_image = os.path.join(self.test_dir, 'empty.png')
        Image.new('RGB', (10, 10), color='black').save(empty_image)
        
        extracted, message = self.stego.extract_data_lsb(empty_image)
        self.assertIsNone(extracted, "Should not extract from clean image")
        
        print("  ✅ Error handling test passed")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
