"""Email templates for OTP and authentication emails."""


class EmailTemplates:
    """Email templates for various authentication scenarios."""

    @staticmethod
    def otp_verification_email(otp_code: str, purpose: str = "email_verification") -> tuple[str, str]:
        """
        Generate OTP verification email template.

        Args:
            otp_code: 6-digit OTP code
            purpose: Purpose of OTP (email_verification or password_reset)

        Returns:
            tuple: (html_body, text_body)
        """
        if purpose == "password_reset":
            subject_context = "Password Reset"
            heading = "Reset Your Password"
            description = "You requested to reset your password. Use the code below to complete the process:"
        else:
            subject_context = "Email Verification"
            heading = "Verify Your Email"
            description = "Thank you for registering! Please use the code below to verify your email address:"

        html_body = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{subject_context}</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
        }}
        .email-container {{
            max-width: 600px;
            margin: 20px auto;
            background-color: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #ffffff;
            padding: 30px 20px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: 600;
        }}
        .content {{
            padding: 40px 30px;
            color: #333333;
        }}
        .content p {{
            line-height: 1.6;
            margin-bottom: 20px;
            font-size: 16px;
        }}
        .otp-box {{
            background-color: #f8f9fa;
            border: 2px dashed #667eea;
            border-radius: 8px;
            padding: 20px;
            margin: 30px 0;
            text-align: center;
        }}
        .otp-code {{
            font-size: 36px;
            font-weight: bold;
            color: #667eea;
            letter-spacing: 8px;
            font-family: 'Courier New', monospace;
        }}
        .expiry-notice {{
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 12px 15px;
            margin: 20px 0;
            font-size: 14px;
            color: #856404;
        }}
        .footer {{
            background-color: #f8f9fa;
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #666666;
            border-top: 1px solid #e9ecef;
        }}
        .footer p {{
            margin: 5px 0;
        }}
        .security-notice {{
            margin-top: 20px;
            padding: 15px;
            background-color: #e7f3ff;
            border-left: 4px solid #2196F3;
            font-size: 14px;
            color: #0c5492;
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>🌙 WisQu Islamic Chatbot</h1>
        </div>
        <div class="content">
            <h2 style="color: #333; margin-top: 0;">{heading}</h2>
            <p>{description}</p>

            <div class="otp-box">
                <p style="margin: 0 0 10px 0; font-size: 14px; color: #666;">Your verification code is:</p>
                <div class="otp-code">{otp_code}</div>
            </div>

            <div class="expiry-notice">
                ⏰ <strong>This code will expire in 10 minutes</strong>
            </div>

            <p>If you didn't request this code, please ignore this email or contact our support team if you have concerns.</p>

            <div class="security-notice">
                🔒 <strong>Security Note:</strong> Never share this code with anyone. WisQu staff will never ask for your verification code.
            </div>
        </div>
        <div class="footer">
            <p><strong>WisQu - Shia Islamic Knowledge Assistant</strong></p>
            <p>Providing authentic Islamic knowledge based on Shia teachings</p>
            <p style="margin-top: 15px;">This is an automated email. Please do not reply to this message.</p>
        </div>
    </div>
</body>
</html>
"""

        text_body = f"""
WisQu Islamic Chatbot - {subject_context}

{heading}

{description}

Your Verification Code:
========================
{otp_code}
========================

⏰ This code will expire in 10 minutes

If you didn't request this code, please ignore this email or contact our support team.

🔒 Security Note: Never share this code with anyone. WisQu staff will never ask for your verification code.

---
WisQu - Shia Islamic Knowledge Assistant
Providing authentic Islamic knowledge based on Shia teachings

This is an automated email. Please do not reply to this message.
"""

        return html_body, text_body

    @staticmethod
    def welcome_email(user_name: str, user_email: str) -> tuple[str, str]:
        """
        Generate welcome email after successful registration.

        Args:
            user_name: User's full name
            user_email: User's email address

        Returns:
            tuple: (html_body, text_body)
        """
        html_body = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to WisQu</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
        }}
        .email-container {{
            max-width: 600px;
            margin: 20px auto;
            background-color: #ffffff;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #ffffff;
            padding: 40px 20px;
            text-align: center;
        }}
        .content {{
            padding: 40px 30px;
            color: #333333;
        }}
        .footer {{
            background-color: #f8f9fa;
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #666666;
        }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="header">
            <h1>🌙 Welcome to WisQu!</h1>
        </div>
        <div class="content">
            <h2>As-salamu alaykum, {user_name or "Dear User"}!</h2>
            <p>Your email has been successfully verified and your account is now active.</p>
            <p>WisQu is your AI-powered companion for authentic Shia Islamic knowledge. Ask questions, explore teachings, and deepen your understanding of Islam.</p>
            <h3>What you can do:</h3>
            <ul>
                <li>💬 Ask questions about Islamic teachings</li>
                <li>📚 Access verified Islamic resources</li>
                <li>🎤 Use voice input for your queries</li>
                <li>🖼️ Generate Islamic art and calligraphy</li>
            </ul>
            <p>If you have any questions or need assistance, our support team is here to help.</p>
            <p style="margin-top: 30px;">Barakallahu feekum!</p>
        </div>
        <div class="footer">
            <p><strong>WisQu - Shia Islamic Knowledge Assistant</strong></p>
        </div>
    </div>
</body>
</html>
"""

        text_body = f"""
Welcome to WisQu!

As-salamu alaykum, {user_name or "Dear User"}!

Your email has been successfully verified and your account is now active.

WisQu is your AI-powered companion for authentic Shia Islamic knowledge.

What you can do:
- Ask questions about Islamic teachings
- Access verified Islamic resources
- Use voice input for your queries
- Generate Islamic art and calligraphy

If you have any questions or need assistance, our support team is here to help.

Barakallahu feekum!

---
WisQu - Shia Islamic Knowledge Assistant
"""

        return html_body, text_body
