from dataclasses import dataclass
@dataclass
class SLA:
    customer_name:str; provider_agent:str; server_class:str; region:str; cpu:float; memory_gb:float
    agreed_price_per_hour:float; requested_max_latency_ms:float; requested_min_availability:float; negotiation_round:int; status:str='ACTIVE'
    def display(self):
        print('\n'+'='*72); print('FINAL SIMULATED SLA'); print('='*72)
        print(f'Customer          : {self.customer_name}')
        print(f'Provider Agent    : {self.provider_agent}')
        print(f'Server Class      : {self.server_class}')
        print(f'Region            : {self.region}')
        print(f'CPU               : {self.cpu:g} vCPU')
        print(f'Memory            : {self.memory_gb:g} GB')
        print(f'Agreed Price      : ${self.agreed_price_per_hour:.4f}/hour')
        print(f'Max Latency       : {self.requested_max_latency_ms:g} ms')
        print(f'Min Availability  : {self.requested_min_availability:g}%')
        print(f'Negotiation Round : {self.negotiation_round}')
        print(f'Status            : {self.status}')
        print('='*72); print('NOTE: This SLA is a SIMULATED research agreement.'); print('='*72)
