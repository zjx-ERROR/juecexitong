#! usr/bin/python3
# -*- coding: utf-8 -*-
import hmac
from utils.dbutils import redis
import json

class TokenMaker:

    def generate_token(self, key, message):
        return hmac.new(str(key).encode('utf-8'), str(message).encode('utf-8'), digestmod='MD5').hexdigest()


class ResolveCacheToken:

    @staticmethod
    def resolve(token):
        try:
            token_seq = redis.get('userID:%s' % token)[5:]
            # token_seq = redis.get('userID:%s' % token)
            res_token = json.loads(token_seq,encoding="utf-8")
        except Exception as e:
            return None
        else:
            invalid_sec = redis.ttl('userID:%s' % token)
            if invalid_sec < 800:
                redis.expire('userID:%s' % token,1800)
            return res_token

if __name__ == "__main__":
    pass