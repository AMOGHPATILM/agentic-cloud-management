from dataclasses import dataclass
@dataclass
class SLARequest:
    customer_name:str
    application_type:str
    required_cpu:int
    required_memory:float
    max_budget:float
    max_latency:float
    min_availability:float
    priority:str='balanced'
