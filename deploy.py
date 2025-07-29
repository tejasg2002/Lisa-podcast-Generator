#!/usr/bin/env python3
"""
Deployment script for LISA Podcast Generator on Modal 1.1
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return None

def check_modal_installed():
    """Check if Modal is installed"""
    try:
        subprocess.run(["modal", "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def main():
    print("🚀 LISA Podcast Generator - Modal 1.1 Deployment")
    print("=" * 50)
    
    # Check if Modal is installed
    if not check_modal_installed():
        print("❌ Modal CLI not found. Please install Modal first:")
        print("   pip install modal>=1.1.0")
        print("   modal token new")
        return
    
    print("✅ Modal CLI found")
    
    # Check if secrets are set
    print("\n🔐 Checking Modal secrets...")
    secrets_check = run_command("modal secret list", "Checking existing secrets")
    
    if "lisa-secrets" not in (secrets_check or ""):
        print("\n⚠️  Modal secrets not found. Please set them up:")
        print("   modal secret create lisa-secrets \\")
        print("     OPENAI_API_KEY='your-openai-key' \\")
        print("     ELEVENLABS_API_KEY='your-elevenlabs-key' \\")
        print("     HEYGEN_API_KEY='your-heygen-key' \\")
        print("     AWS_ACCESS_KEY_ID='your-aws-key' \\")
        print("     AWS_SECRET_ACCESS_KEY='your-aws-secret' \\")
        print("     AWS_S3_BUCKET='your-s3-bucket'")
        return
    
    print("✅ Modal secrets found")
    
    # Deploy the FastAPI app
    print("\n🚀 Deploying FastAPI application...")
    deploy_result = run_command(
        "modal deploy modal_app.py::fastapi_app",
        "Deploying FastAPI app"
    )
    
    if deploy_result:
        print("\n🎉 Deployment successful!")
        print("\n📋 Next steps:")
        print("1. Get your deployment URL:")
        print("   modal app list")
        print("\n2. Test your API:")
        print("   curl -X POST 'https://your-app.modal.run/v1/lisa-audio-podcast' \\")
        print("     -H 'Content-Type: application/json' \\")
        print("     -d '{\"input_type\": \"idea\", \"input_text\": \"AI in 2024\", ...}'")
        print("\n3. Monitor logs:")
        print("   modal app logs lisa-podcast-generator")
    else:
        print("\n❌ Deployment failed. Check the error messages above.")

if __name__ == "__main__":
    main() 