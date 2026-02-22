-- Create database
CREATE DATABASE IF NOT EXISTS secure_pki_steganography;
USE secure_pki_steganography;

-- Create user and grant privileges
CREATE USER IF NOT EXISTS 'stegouser'@'%' IDENTIFIED BY 'stegopassword';
CREATE USER IF NOT EXISTS 'stegouser'@'localhost' IDENTIFIED BY 'stegopassword';

GRANT ALL PRIVILEGES ON secure_pki_steganography.* TO 'stegouser'@'%';
GRANT ALL PRIVILEGES ON secure_pki_steganography.* TO 'stegouser'@'localhost';

-- For root user (XAMPP default)
GRANT ALL PRIVILEGES ON secure_pki_steganography.* TO 'root'@'localhost' IDENTIFIED BY '' WITH GRANT OPTION;

FLUSH PRIVILEGES;
