def proof_of_work(last_proof):
    # Create a variable that we will use to find our next proof of work
    incrementor = last_proof + 1

    # Keep incrementing the incrementor until it's equal to a number divisible by 9
    # and the proof of work of the previous block in the chain
    while not (incrementor % 9 == 0 and incrementor % last_proof == 0):
        incrementor += 1

    # Once that number is found, we can return it as a proof of our work
    return incrementor
