#!/usr/bin/env python3
"""
MSVAI Weekly Reports - Setup Verification Script
This script verifies that all required components are properly configured.
"""

import os
import sys
import json
from pathlib import Path

def check_python_version():
    """Check if Python version is 3.8 or higher"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print(f"✅ Python version: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"❌ Python version: {version.major}.{version.minor}.{version.micro} (Required: 3.8+)")
        return False

def check_virtual_environment():
    """Check if virtual environment is activated"""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment: Activated")
        return True
    else:
        print("⚠️  Virtual environment: Not detected (recommended to use venv)")
        return False

def check_dependencies():
    """Check if required Python packages are installed"""
    required_packages = ['pytz', 'slack_sdk', 'langdetect', 'requests']
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ Package {package}: Installed")
        except ImportError:
            print(f"❌ Package {package}: Missing")
            missing_packages.append(package)

    if missing_packages:
        print(f"\n💡 To install missing packages: pip install {' '.join(missing_packages)}")
        return False
    return True

def check_env_file():
    """Check if .env file exists and contains required variables"""
    env_path = Path('.env')
    if not env_path.exists():
        print("❌ .env file: Missing")
        print("💡 Copy .env.example to .env and fill in your credentials")
        return False

    print("✅ .env file: Found")

    # Check for required environment variables
    with open(env_path, 'r') as f:
        env_content = f.read()

    has_slack_token = 'SLACK_USER_TOKEN=' in env_content and 'xoxp-your-slack-user-token-here' not in env_content
    has_openrouter = 'OPENROUTER_API_KEY=' in env_content

    if has_slack_token:
        print("✅ SLACK_USER_TOKEN: Configured")
    else:
        print("❌ SLACK_USER_TOKEN: Not configured")
        return False

    if has_openrouter and 'your-openrouter-api-key-here' not in env_content:
        print("✅ OPENROUTER_API_KEY: Configured (optional)")
    else:
        print("⚠️  OPENROUTER_API_KEY: Not configured (AI replies disabled)")

    return True

def check_required_files():
    """Check if all required files exist"""
    required_files = [
        'jobs/check_weekly_reports.py',
        'jobs/generate_report_reply.py',
        '.clinerules/companyoverview.md',
        'jobs/serhii_ceo_reply_style.md'
    ]

    all_exist = True
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}: Found")
        else:
            print(f"❌ {file_path}: Missing")
            all_exist = False

    return all_exist

def check_optional_files():
    """Check optional files and create them if needed"""
    optional_files = {
        'jobs/reporter_custom_deadlines.json': '{}',
        'jobs/replied_log.json': '{}',
        'reports': None  # Directory
    }

    for file_path, default_content in optional_files.items():
        path = Path(file_path)

        if file_path == 'reports':
            if not path.exists():
                path.mkdir(exist_ok=True)
                print(f"✅ {file_path}/: Created directory")
            else:
                print(f"✅ {file_path}/: Directory exists")
        else:
            if not path.exists():
                if default_content:
                    with open(path, 'w') as f:
                        f.write(default_content)
                    print(f"✅ {file_path}: Created with default content")
            else:
                print(f"✅ {file_path}: Found")

def check_company_overview():
    """Check if company overview has valid team member data"""
    overview_path = Path('.clinerules/companyoverview.md')
    if not overview_path.exists():
        print("❌ Company overview: File missing")
        return False

    with open(overview_path, 'r') as f:
        content = f.read()

    # Check for the weekly reporting structure section
    if '### Weekly Reporting Structure' in content:
        # Count team members
        team_members = content.count('Slack User ID: U')
        print(f"✅ Company overview: {team_members} team members found")
        return True
    else:
        print("❌ Company overview: Weekly Reporting Structure section not found")
        return False

def run_basic_import_test():
    """Test if the main script can be imported"""
    try:
        sys.path.insert(0, 'jobs')
        import check_weekly_reports
        print("✅ Main script: Can be imported successfully")
        return True
    except Exception as e:
        print(f"❌ Main script: Import failed - {e}")
        return False

def main():
    print("🔍 MSVAI Weekly Reports - Setup Verification\n")

    checks = [
        ("Python Version", check_python_version),
        ("Virtual Environment", check_virtual_environment),
        ("Dependencies", check_dependencies),
        ("Environment File", check_env_file),
        ("Required Files", check_required_files),
        ("Company Overview", check_company_overview),
        ("Script Import", run_basic_import_test),
    ]

    print("Running setup verification checks...\n")

    passed = 0
    total = len(checks)

    for check_name, check_func in checks:
        print(f"\n📋 {check_name}:")
        if check_func():
            passed += 1

    # Handle optional files separately (doesn't count towards pass/fail)
    print(f"\n📋 Optional Files:")
    check_optional_files()

    print(f"\n{'='*50}")
    print(f"Setup Verification Results: {passed}/{total} checks passed")

    if passed == total:
        print("🎉 Setup complete! You can now run: python jobs/check_weekly_reports.py")
        return 0
    else:
        print("⚠️  Please fix the issues above before running the application.")
        print("\n💡 Quick fixes:")
        print("   - Install dependencies: pip install -r requirements.txt")
        print("   - Copy environment file: cp .env.example .env")
        print("   - Edit .env with your actual Slack token")
        return 1

if __name__ == "__main__":
    sys.exit(main())