import os
import json
import hashlib
import sys

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

def verify_audit_chain():
    # Audit log is in the current directory's governance folder if running from backend
    audit_log = os.path.join(os.getcwd(), "governance", "sovereign_audit.log")
    
    if not os.path.exists(audit_log):
        print(f"[VERIFIER] Error: Audit log not found at {audit_log}")
        return False

    print(f"=== Sovereign Audit Chain Verification ===")
    
    expected_previous_hash = "0" * 64
    entry_count = 0
    
    with open(audit_log, "r") as f:
        for idx, line in enumerate(f):
            try:
                entry = json.loads(line.strip())
                recorded_current_hash = entry.pop("current_hash")
                recorded_previous_hash = entry.get("previous_hash")
                
                # Check link to previous
                if recorded_previous_hash != expected_previous_hash:
                    print(f"[!] BROKEN CHAIN at entry {idx}: Expected prev {expected_previous_hash[:8]}, found {recorded_previous_hash[:8]}")
                    return False
                
                # Re-calculate hash
                entry_str = json.dumps(entry, sort_keys=True)
                calculated_hash = hashlib.sha256(entry_str.encode()).hexdigest()
                
                if calculated_hash != recorded_current_hash:
                    print(f"[!] TAMPER DETECTED at entry {idx}: Calculated {calculated_hash[:8]}, found {recorded_current_hash[:8]}")
                    return False
                
                expected_previous_hash = calculated_hash
                entry_count += 1
            except Exception as e:
                print(f"[!] Error parsing entry {idx}: {e}")
                return False

    print(f"COMPLETE: Verified {entry_count} entries. Chain is mathematically valid and untampered.")
    return True

if __name__ == "__main__":
    if verify_audit_chain():
        sys.exit(0)
    else:
        sys.exit(1)
