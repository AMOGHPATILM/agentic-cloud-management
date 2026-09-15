from datetime import datetime
class BaseAgent:
    def __init__(self,agent_name): self.agent_name=agent_name
    def log(self,receiver,message):
        now=datetime.now().strftime('%H:%M:%S')
        print(f'[{now}] {self.agent_name:<24} -> {receiver:<24} | {message}')
