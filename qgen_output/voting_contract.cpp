// A simple, non-vulnerable Voting contract
outputStruct main(inputStruct in) {
    outputStruct out;

    // State:
    // "proposal_text" => string
    // "proposal_votes" => long long
    // [voter_address] => bool (true if they have voted)

    if (in.functionName == "startProposal") {
        char* text = get_string_from_params(in.params, 0);
        save_string_state("proposal_text", text);
        save_long_long_state("proposal_votes", 0);
        // In a real contract, you would also need to clear old voter records
        out.success = true;
    }

    if (in.functionName == "vote") {
        bool has_voted = load_bool_state(in.sender);

        if (!has_voted) {
            long long current_votes = load_long_long_state("proposal_votes");
            save_long_long_state("proposal_votes", current_votes + 1);
            save_bool_state(in.sender, true);
            out.success = true;
        } else {
            // User has already voted
            out.success = false;
        }
    }

    if (in.functionName == "getProposal") {
        char* text = load_string_state("proposal_text");
        long long votes = load_long_long_state("proposal_votes");
        set_string_return(text);
        set_long_long_return(votes);
        out.success = true;
    }

    return out;
}
