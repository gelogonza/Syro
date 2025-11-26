#!/usr/bin/env python
"""
Email Configuration Test Script for Syro
=========================================

This script tests your email configuration to ensure emails can be sent
for user authentication (signup, password reset, etc.)

Usage:
    python test_email.py recipient@example.com
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Syro.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings


def test_email(recipient_email):
    """Test sending an email"""
    print("=" * 60)
    print("Syro Email Configuration Test")
    print("=" * 60)
    print(f"\nCurrent Configuration:")
    print(f"  EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
    print(f"  EMAIL_HOST: {settings.EMAIL_HOST}")
    print(f"  EMAIL_PORT: {settings.EMAIL_PORT}")
    print(f"  EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
    print(f"  EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")
    print(f"  DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
    print(f"  DEBUG: {settings.DEBUG}")
    print()

    if settings.DEBUG and 'console' in settings.EMAIL_BACKEND.lower():
        print("⚠️  Development Mode: Emails will print to console")
        print("   (This is normal for local development)")
        print()

    try:
        print(f"Sending test email to: {recipient_email}")
        print("Please wait...")
        
        send_mail(
            subject='Syro Email Test - Authentication Setup',
            message=(
                'This is a test email from Syro.\n\n'
                'If you received this email, your email configuration is working correctly!\n\n'
                'This means:\n'
                '- User signup emails will work\n'
                '- Password reset emails will work\n'
                '- Email verification will work\n\n'
                'Your Syro authentication system is ready to go! 🎵'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        
        print("\n✅ SUCCESS! Email sent successfully!")
        
        if settings.DEBUG and 'console' in settings.EMAIL_BACKEND.lower():
            print("\n📧 Check the console output above to see the email content.")
        else:
            print(f"\n📧 Check your inbox at {recipient_email}")
            print("   (Don't forget to check spam/junk folder)")
        
        print("\n✨ Your email configuration is working correctly!")
        print("   Users can now sign up and reset passwords.")
        
    except Exception as e:
        print("\n❌ ERROR: Failed to send email!")
        print(f"   Error: {str(e)}")
        print("\n🔧 Troubleshooting:")
        
        if 'console' not in settings.EMAIL_BACKEND.lower():
            print("   1. Check your .env file has correct EMAIL_* settings")
            print("   2. For Gmail, use an App Password (not your regular password)")
            print("      https://support.google.com/accounts/answer/185833")
            print("   3. Verify EMAIL_HOST_USER and EMAIL_HOST_PASSWORD are correct")
            print("   4. Check if your email provider requires specific settings")
            print("   5. Ensure EMAIL_USE_TLS or EMAIL_USE_SSL is correctly set")
        else:
            print("   1. This error shouldn't happen in console mode")
            print("   2. Check Django settings.py for email configuration")
        
        sys.exit(1)
    
    print("\n" + "=" * 60)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python test_email.py recipient@example.com")
        print("\nExample:")
        print("  python test_email.py your-email@gmail.com")
        sys.exit(1)
    
    recipient = sys.argv[1]
    
    # Basic email validation
    if '@' not in recipient or '.' not in recipient:
        print(f"❌ Invalid email address: {recipient}")
        sys.exit(1)
    
    test_email(recipient)
