from importlib import resources  
from typing import Dict, Type  
import inspect  

def discover_tools() -> Dict[str, object]:  
    tools = {}  
    for resource in resources.contents(__name__):  
        if resource.endswith(".py") and resource != "__init__.py":  
            module_name = f"{__name__}.{resource[:-3]}"  
            module = __import__(module_name, fromlist=[""])  
            for name, obj in inspect.getmembers(module):  
                if inspect.isfunction(obj) and not name.startswith("_"):  
                    tools[name] = obj  
    return tools  