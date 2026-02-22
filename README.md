# 🔐 SecurePixel

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![Platform](https://img.shields.io/badge/platform-windows%20%7C%20linux%20%7C%20macos-lightgrey)]()

A secure document signing and message transfer system with Public Key Infrastructure (PKI) and steganography. Hide encrypted messages in images, sign documents digitally, and communicate securely.

## 📋 Table of Contents
- [Features](#features)
- [Quick Start with Docker](#quick-start-with-docker)
- [Manual Installation](#manual-installation)
- [Documentation](#documentation)
- [License](#license)
- [Contributing](#contributing)

## ✨ Features
- ✅ **PKI-based Authentication** - Digital certificates for all users
- ✅ **Certificate Authority** - Issue and manage digital certificates
- ✅ **Document Signing** - Sign documents with RSA private keys
- ✅ **Signature Verification** - Verify signed documents
- ✅ **LSB Steganography** - Hide data in images
- ✅ **Secure Messaging** - Encrypted messages with attachments
- ✅ **File Support** - Hide any file type in images
- ✅ **Built-in File Viewer** - View text, images, and binary files
- ✅ **Security Audit** - Comprehensive security testing
- ✅ **Docker Support** - Easy deployment with containers
- ✅ **phpMyAdmin** - Database management interface
- ✅ **Cross-Platform** - Windows, Linux, macOS

## 🚀 Quick Start with Docker

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows/Mac) or Docker Engine (Linux)
- Docker Compose (included with Docker Desktop)
- 4GB RAM minimum
- X11 Server (for GUI - see platform-specific instructions below)

### One-Command Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Sara-Dangol/SecurePixel.git
   cd SecurePixel