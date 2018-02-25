import datetime as date
import json
from flask import Flask, request
from block_util import create_genesis_block
from block import Block
import requests
import sys
from pow import proof_of_work

node = Flask(__name__)

# A completely random address of the owner of this node
miner_address = "q3nf394hjg-random-miner-address-34nf3i4nflkn3oi"
# This node's blockchain copy
blockchain = []
# Store the transactions that this node has in a list
this_nodes_transactions = []
# Store the url data of every other node in the network
# so that we can communicate with them
peer_nodes = []


@node.route('/txion', methods=['POST'])
def transactions():
    if request.method == 'POST':
        # On each new POST request we extract the transaction data
        new_txion = request.get_json()

        # Then we add the transaction to our list
        this_nodes_transactions.append(new_txion)

        # Because the transaction was successfully submitted, we log it to our console
        print("New transaction")
        print("FROM: {}".format(new_txion['from']))
        print("TO: {}".format(new_txion['to']))
        print("AMOUNT: {}\n".format(new_txion['amount']))

        # Then we let the client know it worked out
        return "Transaction submission successful\n"


@node.route('/mine', methods=['GET'])
def mine():
    # Get the last proof of work
    last_block = blockchain[len(blockchain) - 1]
    last_proof = last_block.data['proof-of-work']

    # Find the proof of work for the current block being mined
    proof = proof_of_work(last_proof)

    # Once we find a valid proof of work, we know we can mine a block so
    # we reward the miner by adding a transaction
    this_nodes_transactions.append(
        {"from": "network", "to": miner_address, "amount": 1}
    )

    # Now we can gather the data needed to create the new block
    new_block_data = {
        "proof-of-work": proof,
        "transactions": list(this_nodes_transactions)
    }

    new_block_index = last_block.index + 1
    new_block_timestamp = date.datetime.now()
    last_block_hash = last_block.hash

    # Empty transaction list
    this_nodes_transactions[:] = []

    # Now create the new block!
    mined_block = Block(
        new_block_index,
        new_block_timestamp,
        new_block_data,
        last_block_hash
    )

    blockchain.append(mined_block)

    # Let the client know we mined a block
    return json.dumps({
        "index": new_block_index,
        "timestamp": str(new_block_timestamp),
        "data": new_block_data,
        "hash": last_block_hash
    }) + "\n"


@node.route('/blocks', methods=['GET'])
def get_blocks():
    chain_to_send = []

    # Convert our blocks into dictionaries so we can send them as json objects later
    for block in consensus():
        chain_to_send.append({
            "index": str(block.index),
            "timestamp": str(block.timestamp),
            "data": str(block.data),
            "hash": block.hash,
        })

    # Send our chain to whomever requested it
    return json.dumps(chain_to_send)


# Update the current blockchain to the longest blockchain across all other peer nodes.
def consensus():
    global blockchain
    longest_chain = blockchain
    for chain in find_other_chains():
        if len(longest_chain) < len(chain):
            longest_chain = chain
    return update_blockchain(longest_chain)


# Updates current blockchain. If updated is needed, converts JSON blockchain to list of blocks.
def update_blockchain(src):
    if len(src) <= len(blockchain):
        return blockchain
    ret = []
    for block in src:
        ret.append(Block(block['index'], block['timestamp'], block['data'], block['hash']))
    return ret


def find_other_chains():
    ret = []
    for peer in peer_nodes:
        response = requests.get('http://%s/blocks' % peer)
        if response.status_code == 200:
            print("blocks from peer: " + response.content)
            ret.append(json.loads(response.content))
    return ret


@node.route('/add_peer', methods=['GET'])
def add_peer():
    host = request.args['host'] if 'host' in request.args else 'localhost'
    port = request.args['port']
    peer = host + ':' + port
    peer_nodes.append(peer)
    print("Peer added: %s" % peer)
    return ""


def main():
    port = 5000
    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    blockchain.append(create_genesis_block())
    node.run(port=port)


if __name__ == '__main__':
    main()
