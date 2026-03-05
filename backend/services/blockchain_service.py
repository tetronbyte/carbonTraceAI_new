import hashlib
import json
import uuid
import qrcode
import os
from typing import List, Dict, Any
from datetime import datetime, timezone
from pathlib import Path
from config import settings

def compute_hash(data: str) -> str:
    """Compute SHA256 hash of data"""
    return hashlib.sha256(data.encode()).hexdigest()

def build_merkle_tree(data_hashes: List[str]) -> str:
    """Build a simple Merkle tree and return root hash"""
    if not data_hashes:
        return compute_hash("")
    
    current_level = data_hashes.copy()
    
    while len(current_level) > 1:
        next_level = []
        for i in range(0, len(current_level), 2):
            left = current_level[i]
            right = current_level[i + 1] if i + 1 < len(current_level) else left
            combined = compute_hash(left + right)
            next_level.append(combined)
        current_level = next_level
    
    return current_level[0]

def serialize_emission_records(records: List[Dict[str, Any]]) -> str:
    """Serialize emission records for hashing"""
    serializable = []
    for record in records:
        serializable.append({
            "id": record.get("id"),
            "energy_type": record.get("energy_type"),
            "quantity": record.get("quantity"),
            "unit": record.get("unit"),
            "scope_type": str(record.get("scope_type")),
            "co2_emissions_kg": record.get("co2_emissions_kg"),
            "invoice_date": record.get("invoice_date").isoformat() if record.get("invoice_date") else None,
        })
    return json.dumps(serializable, sort_keys=True)

def generate_qr_code(verification_url: str, output_path: str) -> str:
    """Generate QR code for verification URL"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(verification_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(output_path)
    
    return output_path

class MockBlockchain:
    """Mock blockchain for demo purposes"""
    
    def __init__(self):
        self.transactions = {}
        self.block_number = 1000000
    
    def record_transaction(self, data_hash: str, merkle_root: str) -> Dict[str, Any]:
        """Simulate recording a transaction on blockchain"""
        tx_hash = "0x" + compute_hash(data_hash + merkle_root + str(datetime.now(timezone.utc)))[:64]
        
        self.block_number += 1
        
        self.transactions[tx_hash] = {
            "data_hash": data_hash,
            "merkle_root": merkle_root,
            "block_number": self.block_number,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        verification_url = f"https://polygonscan.com/tx/{tx_hash}"
        
        return {
            "transaction_hash": tx_hash,
            "block_number": self.block_number,
            "verification_url": verification_url,
            "is_verified": True,
        }
    
    def verify_transaction(self, tx_hash: str) -> Dict[str, Any]:
        """Verify a transaction exists"""
        if tx_hash in self.transactions:
            return {
                "exists": True,
                "data": self.transactions[tx_hash]
            }
        return {"exists": False}

# Global mock blockchain instance
mock_blockchain = MockBlockchain()

def record_on_blockchain(emission_records: List[Dict[str, Any]], organization_id: str) -> Dict[str, Any]:
    """Record emission data on blockchain (mock)"""
    # Serialize and hash records
    serialized = serialize_emission_records(emission_records)
    data_hash = compute_hash(serialized)
    
    # Build Merkle tree
    record_hashes = [compute_hash(json.dumps(r, default=str, sort_keys=True)) for r in emission_records]
    merkle_root = build_merkle_tree(record_hashes)
    
    # Record on mock blockchain
    result = mock_blockchain.record_transaction(data_hash, merkle_root)
    
    # Generate QR code
    qr_filename = f"qr_{uuid.uuid4().hex[:8]}.png"
    qr_path = os.path.join(settings.REPORTS_DIR, "qr_codes", qr_filename)
    generate_qr_code(result["verification_url"], qr_path)
    
    return {
        "data_hash": data_hash,
        "merkle_root": merkle_root,
        "transaction_hash": result["transaction_hash"],
        "block_number": result["block_number"],
        "verification_url": result["verification_url"],
        "qr_code_path": qr_path,
        "is_verified": result["is_verified"],
    }
