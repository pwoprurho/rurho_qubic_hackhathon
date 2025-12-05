// Contract with an intentional access control flaw.
// The scanner must detect that 'wipe_contract_funds' lacks an owner check.
outputStruct main(inputStruct in) {
    outputStruct out;
    
    // Function that should ONLY be callable by the owner, but isn't protected.
    if (in.functionName == "wipe_contract_funds") {
        
        // VULNERABILITY: No is_owner() check. Anyone can call this!
        long long contract_balance = get_contract_balance();
        
        // Transfer all funds to the sender who called the function
        send_funds(in.sender, contract_balance);
        
        out.success = true;
    }
    return out;
}