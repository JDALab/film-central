"""Code from: https://github.com/Ciarands/vidsrc-to-resolver"""
from __future__ import annotations
from typing import TYPE_CHECKING, Dict

if TYPE_CHECKING:
    from typing import Dict, Optional, Union, Tuple, List

    from mov_cli.http_client import HTTPClient

import re
import base64
import json
from mov_cli.errors import MovCliException

__all__ = (
    "VidPlay",
)

class VidPlay():
    def __init__(self, http_client: HTTPClient) -> None:
        self.KEY_URL : str = "https://github.com/JDALab/vidkey-js/blob/main/keys.json"
        self.http_client = http_client
    
    def decode_data(self, key: str, data: Union[bytearray, str]) -> bytearray:
        key_bytes = bytes(key, 'utf-8')
        s = bytearray(range(256))
        j = 0

        for i in range(256):
            j = (j + s[i] + key_bytes[i % len(key_bytes)]) & 0xff
            s[i], s[j] = s[j], s[i]

        decoded = bytearray(len(data))
        i = 0
        k = 0

        for index in range(len(data)):
            i = (i + 1) & 0xff
            k = (k + s[i]) & 0xff
            s[i], s[k] = s[k], s[i]
            t = (s[i] + s[k]) & 0xff

            if isinstance(data[index], str):
                decoded[index] = ord(data[index]) ^ s[t]
            elif isinstance(data[index], int):
                decoded[index] = data[index] ^ s[t]
            else:
                raise RC4DecodeFailure("Unsupported data type in the input")

        return decoded
    
    def int_2_base(self, x: int, base: int) -> str:
        charset = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ+/"

        if x < 0:
            sign = -1
        elif x == 0:
            return 0
        else:
            sign = 1

        x *= sign
        digits = []

        while x:
            digits.append(charset[int(x % base)])
            x = int(x / base)
        
        if sign < 0:
            digits.append('-')
        digits.reverse()

        return ''.join(digits)
    
    def decode_base64_url_safe(s: str) -> bytearray:
        standardized_input = s.replace('_', '/').replace('-', '+')
        binary_data = base64.b64decode(standardized_input)
        return bytearray(binary_data)

    def get_futoken(self, key: str, url: str, provider_url: str) -> str:
        req = self.http_client.get(f"{provider_url}/futoken", {"Referer": url})
        fu_key = re.search(r"var\s+k\s*=\s*'([^']+)'", req.text).group(1)
        
        return f"{fu_key},{','.join([str(ord(fu_key[i % len(fu_key)]) + ord(key[i])) for i in range(len(key))])}"

    def encode_id(self, v_id: str) -> str:
        req = self.http_client.get(self.KEY_URL)
        
        matches = re.search(r"\"rawLines\":\s*\[\"(.+)\"\]", req.text)

        key1, key2 = json.loads(matches.group(1).replace("\\", ""))
        decoded_id = self.decode_data(key1, v_id)
        encoded_result = self.decode_data(key2, decoded_id)
        
        encoded_base64 = base64.b64encode(encoded_result)
        decoded_result = encoded_base64.decode("utf-8")

        return decoded_result.replace("/", "_")
    
    def resolve_source(self, url: str, provider_url: str = "https://vidplay.online") -> Tuple[Optional[List], Optional[Dict]]:
        url_data = url.split("?")

        key = self.encode_id(url_data[0].split("/e/")[-1])
        futoken = self.get_futoken(key, url, provider_url)
        
        req = self.http_client.get(f"{provider_url}/mediainfo/{futoken}?{url_data[1]}&autostart=true", headers={"Referer": url})
        if req.status_code != 200:
            return None, None

        req_data = req.json()
        if (req_data.get("result")) and isinstance(req_data.get("result"), dict):
            sources = req_data.get("result").get("sources")
            return [value.get("file") for value in sources]
        
        return None, None

class RC4DecodeFailure(MovCliException):
    """Raised when failure on decoding RC4 data."""
    def __init__(self) -> None:
        super().__init__(
            "Failed to decode RC4 Data."
        )