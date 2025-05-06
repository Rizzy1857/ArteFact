import hashlib  
import json  
from pathlib import Path  
from rich.console import Console  

console = Console()  

SUPPORTED_ALGORITHMS = {  
    "md5": hashlib.md5,  
    "sha1": hashlib.sha1,  
    "sha256": hashlib.sha256  
}  

def hash_file(file_path: Path, algorithm="sha256") -> str:  
    if algorithm not in SUPPORTED_ALGORITHMS:  
        raise ValueError(f"Unsupported algorithm: {algorithm}")  
    hasher = SUPPORTED_ALGORITHMS[algorithm]()  
    with open(file_path, "rb") as f:  
        for chunk in iter(lambda: f.read(4096), b""):  
            hasher.update(chunk)  
    return hasher.hexdigest()  

def hash_directory(dir_path: Path, algorithm="sha256", output_format="table") -> dict:  
    results = {}  
    for file in dir_path.rglob("*"):  
        if file.is_file():  
            results[str(file)] = hash_file(file, algorithm)  

    if output_format == "json":  
        return json.dumps(results, indent=2)  
    else:  
        table = table(title=f"Hashes ({algorithm.upper()})", show_lines=True)  
        table.add_column("File", style="cyan")  
        table.add_column("Hash", style="green")  
        for file, hash_val in results.items():  
            table.add_row(file, hash_val)  
        console.print(table)  
    return results  