import hashlib
import hmac
import urllib.parse
import datetime
import random
from django.conf import settings


class VNPay:
    def __init__(self):
        self.vnp_TmnCode = settings.VNPAY_CONFIG['vnp_TmnCode']
        self.vnp_HashSecret = settings.VNPAY_CONFIG['vnp_HashSecret']
        self.vnp_Url = settings.VNPAY_CONFIG['vnp_Url']
        self.vnp_ReturnUrl = settings.VNPAY_CONFIG['vnp_ReturnUrl']

    def get_payment_url(self, order_id, amount, order_desc, ip_addr, currency='VND', language='vn'):
        # Build payment URL for VNPay
        vnp_OrderInfo = order_desc
        vnp_OrderType = 'billpayment'
        vnp_Amount = int(amount * 100)  # Convert to VND (no decimal)
        vnp_Locale = language
        vnp_CurrCode = currency
        vnp_IpAddr = ip_addr

        # Generate payment URL
        vnp_Params = {}
        vnp_Params['vnp_Version'] = '2.1.0'
        vnp_Params['vnp_Command'] = 'pay'
        vnp_Params['vnp_TmnCode'] = self.vnp_TmnCode
        vnp_Params['vnp_Amount'] = vnp_Amount
        vnp_Params['vnp_CurrCode'] = vnp_CurrCode
        vnp_Params['vnp_TxnRef'] = order_id
        vnp_Params['vnp_OrderInfo'] = vnp_OrderInfo
        vnp_Params['vnp_OrderType'] = vnp_OrderType

        # Create date string in VNPay format
        vnp_CreateDate = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        vnp_Params['vnp_CreateDate'] = vnp_CreateDate

        # Set return URL for VNPay to redirect after payment
        vnp_Params['vnp_ReturnUrl'] = self.vnp_ReturnUrl
        vnp_Params['vnp_IpAddr'] = vnp_IpAddr
        vnp_Params['vnp_Locale'] = vnp_Locale

        # Sort parameters by key
        vnp_Params = sorted(vnp_Params.items())

        # Generate hash data
        hash_data = urllib.parse.urlencode(vnp_Params, quote_via=urllib.parse.quote)

        # Create secure hash
        secure_hash = self.hmacsha512(self.vnp_HashSecret, hash_data)

        # Append vnp_SecureHash parameter to URL
        vnp_Params.append(('vnp_SecureHash', secure_hash))

        # Build full payment URL
        vnp_Url = self.vnp_Url + "?" + urllib.parse.urlencode(vnp_Params, quote_via=urllib.parse.quote)

        return vnp_Url

    def verify_payment(self, params):
        # Remove vnp_SecureHash from params
        vnp_SecureHash = params.pop('vnp_SecureHash')

        # Sort remaining parameters by key
        params = sorted(params.items())

        # Generate hash data
        hash_data = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)

        # Create secure hash for verification
        secure_hash = self.hmacsha512(self.vnp_HashSecret, hash_data)

        # Compare generated hash with received hash
        return secure_hash == vnp_SecureHash

    def hmacsha512(self, key, data):
        byteKey = key.encode('utf-8')
        byteData = data.encode('utf-8')
        return hmac.new(byteKey, byteData, hashlib.sha512).hexdigest()

    @staticmethod
    def generate_order_id():
        # Generate a unique order ID
        return f"{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(100, 999)}"