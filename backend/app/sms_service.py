# !/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@File    : sms_service.py
@Date    : 2025/9/18 00:31
@Author  : JIAMID
@Contact : jiamid@qq.com
@Desc    : 
"""
import time
import hashlib
import hmac
import requests
import json
import datetime

class TencentSESMailer:
    def __init__(self, secret_id, secret_key, from_email, template_id, region="ap-hongkong"):
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.service = "ses"
        self.host = "ses.tencentcloudapi.com"
        self.region = region
        self.version = "2020-10-02"
        self.action = "SendEmail"
        self.from_email = from_email
        self.template_id = template_id

    def _hmac_sha256(self, key: bytes, msg: str) -> bytes:
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    def _build_auth_headers(self, payload: dict):
        t = datetime.datetime.now(datetime.UTC)
        # timestamp = int(t.timestamp())
        timestamp = int(time.time())
        print(timestamp)
        date = t.strftime("%Y-%m-%d")

        # Step 1: CanonicalRequest
        http_request_method = "POST"
        canonical_uri = "/"
        canonical_querystring = ""
        ct = "application/json; charset=utf-8"

        canonical_headers = f"content-type:{ct}\nhost:{self.host}\n"
        signed_headers = "content-type;host"

        hashed_request_payload = hashlib.sha256(json.dumps(payload).encode("utf-8")).hexdigest()

        canonical_request = (
            f"{http_request_method}\n"
            f"{canonical_uri}\n"
            f"{canonical_querystring}\n"
            f"{canonical_headers}\n"
            f"{signed_headers}\n"
            f"{hashed_request_payload}"
        )

        # Step 2: StringToSign
        algorithm = "TC3-HMAC-SHA256"
        hashed_canonical_request = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
        credential_scope = f"{date}/{self.service}/tc3_request"
        string_to_sign = (
            f"{algorithm}\n"
            f"{timestamp}\n"
            f"{credential_scope}\n"
            f"{hashed_canonical_request}"
        )

        # Step 3: Signature
        secret_date = self._hmac_sha256(("TC3" + self.secret_key).encode("utf-8"), date)
        secret_service = hmac.new(secret_date, self.service.encode("utf-8"), hashlib.sha256).digest()
        secret_signing = hmac.new(secret_service, "tc3_request".encode("utf-8"), hashlib.sha256).digest()
        signature = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

        # Step 4: Authorization
        authorization = (
            f"{algorithm} "
            f"Credential={self.secret_id}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, "
            f"Signature={signature}"
        )

        headers = {
            "Authorization": authorization,
            "Content-Type": ct,
            "Host": self.host,
            "X-TC-Action": self.action,
            "X-TC-Timestamp": str(timestamp),
            "X-TC-Version": self.version,
            "X-TC-Region": self.region,
        }
        return headers

    def send_email(self, email: str, code: str, subject="您收到了新的验证码"):
        payload = {
            "FromEmailAddress": f'JustChatAMoment <{self.from_email}>',
            "Destination": [email],
            "Template": {
                "TemplateID": self.template_id,
                "TemplateData": json.dumps({"code": code})
            },
            "Subject": subject
        }

        headers = self._build_auth_headers(payload)
        resp = requests.post(f"https://{self.host}", headers=headers, data=json.dumps(payload))

        return resp.status_code, resp.text


