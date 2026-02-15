# HTML Email Templates for Meri Panchayat Portal

OTP_TEMPLATE_EN = """
<!DOCTYPE html>
<html>
<head>
<style>
    body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 0; }}
    .container {{ max-width: 500px; margin: 20px auto; background-color: #ffffff; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1); border: 1px solid #e0e0e0; }}
    .header {{ background-color: #3f51b5; color: #ffffff; padding: 20px; text-align: center; font-size: 24px; font-weight: bold; }}
    .content {{ padding: 30px; text-align: center; color: #333333; }}
    .otp-label {{ font-size: 16px; margin-bottom: 20px; color: #666666; }}
    .otp-code-box {{ background-color: #f0f0f0; padding: 15px 25px; border-radius: 5px; display: inline-block; margin: 20px 0; }}
    .otp-code {{ font-size: 36px; font-weight: bold; color: #3f51b5; letter-spacing: 5px; }}
    .footer-text {{ font-size: 14px; color: #777777; line-height: 1.5; margin-top: 20px; }}
    .copyright {{ font-size: 12px; color: #999999; padding: 15px; text-align: center; background-color: #f9f9f9; }}
    .link {{ color: #3f51b5; text-decoration: none; }}
</style>
</head>
<body>
    <div class="container">
        <div class="header">Email OTP</div>
        <div class="content">
            <p class="otp-label">Your One-Time Password (OTP) is:</p>
            <div class="otp-code-box">
                <span class="otp-code">{}</span>
            </div>
            <p class="footer-text">Please use this OTP to complete your login process. Do not share this code with anyone.</p>
        </div>
        <div class="copyright">
            &copy; <a href="http://www.rohiitchouhan.com" class="link">www.rohiitchouhan.com</a>. All rights reserved.
        </div>
    </div>
</body>
</html>
"""

OTP_TEMPLATE_KN = """
<!DOCTYPE html>
<html>
<head>
<style>
    body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 0; }}
    .container {{ max-width: 500px; margin: 20px auto; background-color: #ffffff; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.1); border: 1px solid #e0e0e0; }}
    .header {{ background-color: #3f51b5; color: #ffffff; padding: 20px; text-align: center; font-size: 24px; font-weight: bold; }}
    .content {{ padding: 30px; text-align: center; color: #333333; }}
    .otp-label {{ font-size: 16px; margin-bottom: 20px; color: #666666; }}
    .otp-code-box {{ background-color: #f0f0f0; padding: 15px 25px; border-radius: 5px; display: inline-block; margin: 20px 0; }}
    .otp-code {{ font-size: 36px; font-weight: bold; color: #3f51b5; letter-spacing: 5px; }}
    .footer-text {{ font-size: 14px; color: #777777; line-height: 1.5; margin-top: 20px; }}
    .copyright {{ font-size: 12px; color: #999999; padding: 15px; text-align: center; background-color: #f9f9f9; }}
    .link {{ color: #3f51b5; text-decoration: none; }}
</style>
</head>
<body>
    <div class="container">
        <div class="header">ಇಮೇಲ್ ಒಟಿಪಿ (Email OTP)</div>
        <div class="content">
            <p class="otp-label">ನಿಮ್ಮ ಒನ್-ಟೈಮ್ ಪಾಸ್‌ವರ್ಡ್ (OTP):</p>
            <div class="otp-code-box">
                <span class="otp-code">{}</span>
            </div>
            <p class="footer-text">ಲಾಗಿನ್ ಪ್ರಕ್ರಿಯೆಯನ್ನು ಪೂರ್ಣಗೊಳಿಸಲು ಈ ಒಟಿಪಿ ಬಳಸಿ. ಈ ಕೋಡ್ ಅನ್ನು ಯಾರೊಂದಿಗೂ ಹಂಚಿಕೊಳ್ಳಬೇಡಿ.</p>
        </div>
        <div class="copyright">
            &copy; <a href="http://www.rohiitchouhan.com" class="link">www.rohiitchouhan.com</a>. ಎಲ್ಲಾ ಹಕ್ಕುಗಳನ್ನು ಕಾಯ್ದಿರಿಸಲಾಗಿದೆ.
        </div>
    </div>
</body>
</html>
"""

EMAIL_TEMPLATES = {
    "en": OTP_TEMPLATE_EN,
    "kn": OTP_TEMPLATE_KN
}
