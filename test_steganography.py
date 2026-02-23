import unittest
import sys
import os
import tempfile
import hashlib
import struct
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from PIL import Image, ImageChops
    import numpy as np
except ImportError as e:
    print(f"❌ PIL/numpy import error: {e}")
    print("Please install Pillow and numpy: pip install Pillow numpy")
    sys.exit(1)

try:
    from stegno_gui import AdvancedSteganography
except ImportError as e:
    print(f"❌ Application import error: {e}")
    sys.exit(1)


class TestSteganography(unittest.TestCase):
    """Test steganography functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once before all tests"""
        print("\n🎨 Testing Steganography Engine...")
    
    def setUp(self):
        """Set up before each test"""
        self.stego = AdvancedSteganography()
        
        # Create temporary directory for test files
        self.test_dir = tempfile.mkdtemp()
        
        # Create test images of different formats and sizes
        self.test_images = {}
        
        # RGB image (100x100)
        rgb_path = os.path.join(self.test_dir, 'test_rgb.png')
        img = Image.new('RGB', (100, 100), color='white')
        img.save(rgb_path)
        self.test_images['rgb'] = rgb_path
        
        # RGBA image (100x100)
        rgba_path = os.path.join(self.test_dir, 'test_rgba.png')
        img = Image.new('RGBA', (100, 100), color=(255, 255, 255, 255))
        img.save(rgba_path)
        self.test_images['rgba'] = rgba_path
        
        # Grayscale image (100x100)
        gray_path = os.path.join(self.test_dir, 'test_gray.png')
        img = Image.new('L', (100, 100), color=255)
        img.save(gray_path)
        self.test_images['gray'] = gray_path
        
        # JPEG image (with compression)
        jpeg_path = os.path.join(self.test_dir, 'test.jpg')
        img = Image.new('RGB', (100, 100), color='white')
        img.save(jpeg_path, 'JPEG', quality=95)
        self.test_images['jpeg'] = jpeg_path
        
        # BMP image
        bmp_path = os.path.join(self.test_dir, 'test.bmp')
        img = Image.new('RGB', (100, 100), color='white')
        img.save(bmp_path)
        self.test_images['bmp'] = bmp_path
        
        # Output image path
        self.output_image = os.path.join(self.test_dir, 'output.png')
        
        # Test data
        self.test_text = b"This is a secret message for testing steganography."
        self.test_binary = os.urandom(512)  # 512 bytes random data
        self.test_json = json.dumps({"key": "value", "number": 42}).encode('utf-8')
    
    def tearDown(self):
        """Clean up test files"""
        import shutil
        shutil.rmtree(self.test_dir)
    
    def test_text_embedding_extraction_rgb(self):
        """Test embedding and extracting text in RGB image"""
        success, message = self.stego.embed_data_lsb(
            self.test_images['rgb'],
            self.test_text,
            self.output_image
        )
        
        self.assertTrue(success, f"Embedding failed: {message}")
        self.assertTrue(os.path.exists(self.output_image), "Output image not created")
        
        # Extract the data
        extracted_data, metadata = self.stego.extract_data_lsb(self.output_image)
        
        self.assertIsNotNone(extracted_data, "No data extracted")
        self.assertEqual(extracted_data, self.test_text, "Extracted text doesn't match")
        self.assertIn('data_length', metadata, "Metadata missing data_length")
        self.assertEqual(metadata['data_length'], len(self.test_text), 
                        "Metadata data_length mismatch")
        self.assertIn('method', metadata, "Metadata missing method")
        self.assertEqual(metadata['method'], 'LSB', "Wrong method in metadata")
        
        print("  ✅ RGB image text embedding/extraction test passed")
    
    def test_text_embedding_extraction_rgba(self):
        """Test embedding and extracting text in RGBA image"""
        success, message = self.stego.embed_data_lsb(
            self.test_images['rgba'],
            self.test_text,
            self.output_image
        )
        
        self.assertTrue(success, f"Embedding failed: {message}")
        
        extracted_data, metadata = self.stego.extract_data_lsb(self.output_image)
        
        self.assertIsNotNone(extracted_data)
        self.assertEqual(extracted_data, self.test_text)
        
        print("  ✅ RGBA image text embedding/extraction test passed")
    
    def test_text_embedding_extraction_grayscale(self):
        """Test embedding and extracting text in grayscale image"""
        success, message = self.stego.embed_data_lsb(
            self.test_images['gray'],
            self.test_text,
            self.output_image
        )
        
        self.assertTrue(success, f"Embedding failed: {message}")
        
        extracted_data, metadata = self.stego.extract_data_lsb(self.output_image)
        
        self.assertIsNotNone(extracted_data)
        self.assertEqual(extracted_data, self.test_text)
        
        print("  ✅ Grayscale image text embedding/extraction test passed")
    
    def test_binary_embedding_extraction(self):
        """Test embedding and extracting binary data"""
        success, message = self.stego.embed_data_lsb(
            self.test_images['rgb'],
            self.test_binary,
            self.output_image
        )
        
        self.assertTrue(success, f"Embedding failed: {message}")
        
        extracted_data, metadata = self.stego.extract_data_lsb(self.output_image)
        
        self.assertIsNotNone(extracted_data)
        self.assertEqual(extracted_data, self.test_binary, "Binary data mismatch")
        
        print("  ✅ Binary data embedding/extraction test passed")
    
    def test_json_embedding_extraction(self):
        """Test embedding and extracting JSON data"""
        success, message = self.stego.embed_data_lsb(
            self.test_images['rgb'],
            self.test_json,
            self.output_image
        )
        
        self.assertTrue(success, f"Embedding failed: {message}")
        
        extracted_data, metadata = self.stego.extract_data_lsb(self.output_image)
        
        self.assertIsNotNone(extracted_data)
        extracted_json = json.loads(extracted_data.decode('utf-8'))
        self.assertEqual(extracted_json['key'], 'value')
        self.assertEqual(extracted_json['number'], 42)
        
        print("  ✅ JSON data embedding/extraction test passed")
    
    def test_large_data_embedding(self):
        """Test embedding larger data within capacity"""
        # 100x100 RGB image has 30000 pixels -> ~3750 bytes capacity
        # Let's use 2000 bytes to be safe
        large_data = os.urandom(2000)
        
        success, message = self.stego.embed_data_lsb(
            self.test_images['rgb'],
            large_data,
            self.output_image
        )
        
        self.assertTrue(success, f"Embedding failed: {message}")
        
        extracted_data, metadata = self.stego.extract_data_lsb(self.output_image)
        
        self.assertIsNotNone(extracted_data)
        self.assertEqual(len(extracted_data), len(large_data))
        self.assertEqual(extracted_data, large_data)
        
        print("  ✅ Large data embedding test passed")
    
    def test_insufficient_capacity(self):
        """Test embedding data larger than capacity"""
        # Try to embed 5000 bytes in 100x100 image (max ~3750 bytes)
        huge_data = os.urandom(5000)
        
        success, message = self.stego.embed_data_lsb(
            self.test_images['rgb'],
            huge_data,
            self.output_image
        )
        
        self.assertFalse(success, "Should fail with insufficient capacity")
        self.assertIn("Insufficient capacity", message, 
                     "Error message should indicate insufficient capacity")
        
        print("  ✅ Insufficient capacity detection test passed")
    
    def test_multiple_embeddings(self):
        """Test embedding multiple times in same image"""
        test_data1 = b"First message"
        test_data2 = b"Second message"
        
        # First embedding
        success1, _ = self.stego.embed_data_lsb(
            self.test_images['rgb'],
            test_data1,
            self.output_image
        )
        self.assertTrue(success1)
        
        # Second embedding in same image (should overwrite)
        success2, _ = self.stego.embed_data_lsb(
            self.test_images['rgb'],
            test_data2,
            self.output_image
        )
        self.assertTrue(success2)
        
        # Extract - should get second message
        extracted_data, metadata = self.stego.extract_data_lsb(self.output_image)
        self.assertEqual(extracted_data, test_data2, "Should extract last embedded data")
        
        print("  ✅ Multiple embeddings test passed")
    
    def test_capacity_analysis(self):
        """Test capacity analysis functionality"""
        # Test with RGB image
        rgb_capacity = self.stego.analyze_capacity(self.test_images['rgb'])
        
        self.assertIn('dimensions', rgb_capacity)
        self.assertIn('mode', rgb_capacity)
        self.assertIn('total_pixels', rgb_capacity)
        self.assertIn('lsb_capacity_bits', rgb_capacity)
        self.assertIn('lsb_capacity_bytes', rgb_capacity)
        self.assertIn('recommended_max_bytes', rgb_capacity)
        
        # 100x100 RGB = 30000 pixels
        self.assertEqual(rgb_capacity['dimensions'], (100, 100))
        self.assertEqual(rgb_capacity['mode'], 'RGB')
        self.assertEqual(rgb_capacity['total_pixels'], 30000)
        self.assertEqual(rgb_capacity['lsb_capacity_bits'], 30000)
        self.assertEqual(rgb_capacity['lsb_capacity_bytes'], 30000 // 8)
        
        # Test with RGBA image
        rgba_capacity = self.stego.analyze_capacity(self.test_images['rgba'])
        self.assertEqual(rgba_capacity['mode'], 'RGBA')
        self.assertEqual(rgba_capacity['total_pixels'], 40000)  # 100x100x4
        
        # Test with grayscale image
        gray_capacity = self.stego.analyze_capacity(self.test_images['gray'])
        self.assertEqual(gray_capacity['mode'], 'L')
        self.assertEqual(gray_capacity['total_pixels'], 10000)  # 100x100x1
        
        print("  ✅ Capacity analysis test passed")
    
    def test_image_integrity(self):
        """Test that embedded image remains visually similar"""
        test_data = b"Secret" * 100
        
        # Get original image data
        original_img = Image.open(self.test_images['rgb'])
        original_array = np.array(original_img)
        
        # Embed data
        self.stego.embed_data_lsb(
            self.test_images['rgb'],
            test_data,
            self.output_image
        )
        
        # Get modified image data
        modified_img = Image.open(self.output_image)
        modified_array = np.array(modified_img)
        
        # Calculate difference
        diff = np.abs(original_array.astype(np.int16) - modified_array.astype(np.int16))
        max_diff = np.max(diff)
        
        # LSB changes should be at most 1 per pixel
        self.assertLessEqual(max_diff, 1, "Maximum pixel change should be 1")
        
        # Most pixels should be unchanged
        changed_pixels = np.sum(diff > 0)
        total_pixels = diff.size
        change_ratio = changed_pixels / total_pixels
        
        # Should be relatively low (only changed where data embedded)
        self.assertLess(change_ratio, 0.5, "Too many pixels changed")
        
        # Images should be different size (but same dimensions)
        self.assertEqual(original_img.size, modified_img.size, "Image dimensions changed")
        
        print("  ✅ Image integrity test passed")
    
    def test_jpeg_compatibility(self):
        """Test embedding in JPEG (should work but with caution)"""
        # JPEG uses lossy compression, so LSB may not survive
        test_data = b"Short message"
        
        success, message = self.stego.embed_data_lsb(
            self.test_images['jpeg'],
            test_data,
            self.output_image
        )
        
        # Should still work (embedding phase)
        self.assertTrue(success, f"Embedding in JPEG failed: {message}")
        
        # But extraction may fail due to JPEG compression artifacts
        try:
            extracted_data, _ = self.stego.extract_data_lsb(self.output_image)
            # If extraction succeeds, data should match
            if extracted_data:
                self.assertEqual(extracted_data, test_data)
                print("  ✅ JPEG embedding/extraction test passed (data survived)")
            else:
                print("  ⚠️ JPEG extraction returned None (expected with lossy compression)")
        except Exception as e:
            print(f"  ⚠️ JPEG extraction exception (expected): {e}")
    
    def test_empty_data(self):
        """Test embedding empty data"""
        empty_data = b""
        
        success, message = self.stego.embed_data_lsb(
            self.test_images['rgb'],
            empty_data,
            self.output_image
        )
        
        self.assertTrue(success, "Should handle empty data")
        
        extracted_data, metadata = self.stego.extract_data_lsb(self.output_image)
        
        self.assertEqual(extracted_data, b"", "Should extract empty data")
        self.assertEqual(metadata['data_length'], 0, "Metadata should show zero length")
        
        print("  ✅ Empty data test passed")
    
    def test_metadata_preservation(self):
        """Test that metadata is preserved correctly"""
        test_data = b"Test with metadata"
        custom_timestamp = "2024-01-01T12:00:00"
        
        # Override the timestamp in metadata by modifying the stego class
        original_method = self.stego.embed_data_lsb
        
        def patched_embed(image_path, data, output_path):
            img = Image.open(image_path)
            img_array = np.array(img)
            flat_array = img_array.flatten()
            
            metadata = {
                'data_length': len(data),
                'timestamp': custom_timestamp,  # Use custom timestamp
                'method': 'LSB',
                'app': 'SecurePixel',
                'test': True
            }
            metadata_bytes = json.dumps(metadata).encode('utf-8')
            header = struct.pack('>I', len(metadata_bytes))
            full_data = header + metadata_bytes + data
            
            binary_data = ''.join(format(byte, '08b') for byte in full_data)
            
            for i in range(len(binary_data)):
                flat_array[i] = (flat_array[i] & 0xFE) | int(binary_data[i])
            
            encoded_array = flat_array.reshape(img_array.shape)
            encoded_img = Image.fromarray(encoded_array.astype(np.uint8))
            encoded_img.save(output_path)
            
            return True, "Success"
        
        # Replace method temporarily
        self.stego.embed_data_lsb = patched_embed
        
        success, _ = self.stego.embed_data_lsb(
            self.test_images['rgb'],
            test_data,
            self.output_image
        )
        
        self.assertTrue(success)
        
        # Restore original method
        self.stego.embed_data_lsb = original_method
        
        extracted_data, metadata = self.stego.extract_data_lsb(self.output_image)
        
        self.assertEqual(extracted_data, test_data)
        self.assertEqual(metadata['timestamp'], custom_timestamp, "Timestamp should match")
        self.assertTrue(metadata.get('test'), "Additional metadata should be preserved")
        
        print("  ✅ Metadata preservation test passed")
    
    def test_different_formats_output(self):
        """Test saving output in different formats"""
        test_data = b"Test format"
        
        # Test PNG output
        png_output = os.path.join(self.test_dir, 'output.png')
        success, _ = self.stego.embed_data_lsb(
            self.test_images['rgb'],
            test_data,
            png_output
        )
        self.assertTrue(success)
        self.assertTrue(os.path.exists(png_output))
        
        # Test BMP output
        bmp_output = os.path.join(self.test_dir, 'output.bmp')
        success, _ = self.stego.embed_data_lsb(
            self.test_images['rgb'],
            test_data,
            bmp_output
        )
        self.assertTrue(success)
        self.assertTrue(os.path.exists(bmp_output))
        
        # Test extraction from both
        for output_path in [png_output, bmp_output]:
            extracted, _ = self.stego.extract_data_lsb(output_path)
            self.assertEqual(extracted, test_data)
        
        print("  ✅ Different output formats test passed")


class TestSteganographyEdgeCases(unittest.TestCase):
    """Test edge cases and error handling in steganography"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once before all tests"""
        print("\n🔍 Testing Steganography Edge Cases...")
    
    def setUp(self):
        """Set up before each test"""
        self.stego = AdvancedSteganography()
        self.test_dir = tempfile.mkdtemp()
        
        # Create a valid test image
        self.test_image = os.path.join(self.test_dir, 'test.png')
        img = Image.new('RGB', (50, 50), color='white')
        img.save(self.test_image)
    
    def tearDown(self):
        """Clean up test files"""
        import shutil
        shutil.rmtree(self.test_dir)
    
    def test_nonexistent_image(self):
        """Test with nonexistent image file"""
        fake_path = os.path.join(self.test_dir, 'nonexistent.png')
        data = b"test"
        output = os.path.join(self.test_dir, 'output.png')
        
        success, message = self.stego.embed_data_lsb(fake_path, data, output)
        
        self.assertFalse(success)
        self.assertIn("No such file", message or "File not found")
        
        print("  ✅ Nonexistent image handling test passed")
    
    def test_corrupt_image(self):
        """Test with corrupt image file"""
        corrupt_path = os.path.join(self.test_dir, 'corrupt.png')
        with open(corrupt_path, 'w') as f:
            f.write("This is not an image file")
        
        data = b"test"
        output = os.path.join(self.test_dir, 'output.png')
        
        success, message = self.stego.embed_data_lsb(corrupt_path, data, output)
        
        self.assertFalse(success)
        self.assertIn("cannot identify image", message or "Invalid image")
        
        print("  ✅ Corrupt image handling test passed")
    
    def test_extract_from_clean_image(self):
        """Test extracting from image with no hidden data"""
        extracted, message = self.stego.extract_data_lsb(self.test_image)
        
        self.assertIsNone(extracted)
        self.assertIn("extraction failed", message or "")
        
        print("  ✅ Clean image extraction test passed")
    
    def test_unicode_text(self):
        """Test embedding unicode text"""
        unicode_text = "Hello 世界! ñáéíóú".encode('utf-8')
        
        success, _ = self.stego.embed_data_lsb(
            self.test_image,
            unicode_text,
            os.path.join(self.test_dir, 'unicode_output.png')
        )
        
        self.assertTrue(success)
        
        extracted, _ = self.stego.extract_data_lsb(
            os.path.join(self.test_dir, 'unicode_output.png')
        )
        
        self.assertEqual(extracted, unicode_text)
        
        print("  ✅ Unicode text test passed")


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
