from cryptography.fernet import Fernet
import platform
import threading 
import requests 
import time
import rsa 
import os 

OS = ""


class Client:
    
    def _key_gen(self) -> None:

        (pubkey, privkey) = rsa.newkeys(512)

        with open("private.pem", "wb") as f:
            f.write(privkey.save_pkcs1())
            
        with open("public.pem", "wb") as f:
            f.write(pubkey.save_pkcs1())
    
    
    def __init__(self, username: str):
        self.server = input("server ip: \n") 
        self.port = input("server port: \n") 
        self.username = username 
        
        self.base_url = f"http://{self.server}:{self.port}"
        
        self.talk_url = f"{self.base_url}/talk"
        self.info_url = f"{self.base_url}/update"
        self.key_url = f"{self.base_url}/get_key"

        self.pubkey = None 
        self.privkey = None
        self.symetric_key = None 
        self.fernet = None
        
        
    def send_info(self):
        
        while True:
            user_input = input("You're message: ")
            message = f'{self.username}: {user_input}'
            requests.post(self.talk_url, data={
                "text": self.fernet.encrypt(message.encode()),
                "username": self.username
            })
            
            
    def update_info(self):
        last_try = None
        while True:
            time.sleep(0.05)
            r = requests.post(self.info_url)
            if last_try == r.json():
                continue 
            last_try = r.json()
            os.system("clear")
            if len(last_try['status']) > 0:
                i = 0
                for msg in last_try["status"]:
                    actual_message = self.fernet.decrypt(msg.encode()).decode("utf-8")
                    if i == 0:
                        users = last_try["users_in_chat"]
                        print(f"Users in chat: {users}\n\n")
                        print(f"{actual_message}\n")
                    else:
                        print(f"{actual_message}\n")
                    i += 1
                
                
    def _key_request(self) -> None:
        with open('private.pem', 'rb') as f:
            self.privkey = rsa.PrivateKey.load_pkcs1(f.read())
        
        with open("public.pem", 'rb') as f:
            with requests.get(self.key_url, data={"pubkey": f.read(), "username": self.username}, stream=True) as r:
                message = r.raw.read(999)
                self.symetric_key = rsa.decrypt(message, self.privkey)
                self.fernet = Fernet(self.symetric_key)

                
                
    def _remove_keys(self) -> None:
        os.remove("private.pem")
        os.remove("public.pem")
                
                
    def _validate_keys(self) -> None:
        
        self._key_gen()
        self._key_request()
        
        with open('public.pem', "rb") as f:
            first_key = f.read()
            
        self.pubkey = rsa.PublicKey.load_pkcs1(first_key)
        self._remove_keys()
        
            
    def __call__(self):
        
        self._validate_keys()
          
        threads = [
            threading.Thread(target=self.send_info),
            threading.Thread(target=self.update_info)
        ]
        
        for th in threads:
            th.start()
        
        
if __name__ == '__main__':
    c = Client(input("Who are you? \t"))
    c()
