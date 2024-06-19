# https://timberry.dev/posts/fastapi-with-apikeys/
'''
This file is basically a placeholder for whatever backend database integration you want to use. 
Right now, it implements the methods we needs, and contains a hard-coded set of API keys and users.
'''
api_keys = {
        "e54d4431-5dab-474e-b71a-0db1fcb9e659": "7oDYjo3d9r58EJKYi5x4E8",
        "5f0c7127-3be9-4488-b801-c7b6415b45e9": "mUP7PpTHmFAkxcQLWKMY8t"
    }
    
users = {
    "7oDYjo3d9r58EJKYi5x4E8": {
        "name": "Bob"
    },
    "mUP7PpTHmFAkxcQLWKMY8t": {
        "name": "Alice"
    },
}

def check_api_key(api_key: str):
    return api_key in api_keys

def get_user_from_api_key(api_key: str):
    return users[api_keys[api_key]]