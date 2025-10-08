# api/routes.py

from flask import Blueprint, jsonify, request
from uuid import uuid4

# Import Blockchain Class from the 'core' package
from core.blockchain import Blockchain 

# Initialize Blockchain and Node ID
blockchain = Blockchain()
node_identifier = str(uuid4()).replace('-', "")

# Create the Blueprint
api_bp = Blueprint('api', __name__)

# --- API Endpoints ---

@api_bp.route('/blockchain', methods=['GET'])
def full_chain():
    """Returns the complete blockchain and its length."""
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }
    return jsonify(response), 200

@api_bp.route('/mine', methods=['GET'])
def mine_block():
    """Mines a new block."""
    # 1. Give mining reward
    blockchain.add_transaction(
        sender="0",  # "0" signifies the system reward
        recipient=node_identifier,
        amount=1
    )
    
    # 2. Perform Proof of Work (PoW)
    last_block_hash = blockchain.hash_block(blockchain.last_block)
    index = len(blockchain.chain)
    nonce = blockchain.proof_of_work(index, last_block_hash, blockchain.current_transactions)
    
    # 3. Add the new block to the chain
    block = blockchain.append_block(nonce, last_block_hash)
    
    response = {
        'message': "New Block has been added (mined)",
        'index': block['index'],
        'hash_of_previous_block': block['hash_of_previous_block'],
        'nonce': block['nonce'],
        'transaction': block['transaction']
    }
    return jsonify(response), 200

@api_bp.route('/transaction/new', methods=['POST'])
def new_transaction():
    """Creates a new transaction. POST body must be JSON."""
    values = request.get_json()
    
    required_fields = ['sender', 'recipient', 'amount']
    # Check for complete data
    if not all(k in values for k in required_fields):
        return jsonify({'error': 'Missing fields: "sender", "recipient", or "amount"'}), 400
    
    # Add the transaction
    index = blockchain.add_transaction(
        values['sender'],
        values['recipient'],
        values['amount']
    )
    
    response = {
        'message': f'Transaction will be added to Block {index}'
    }
    return jsonify(response), 201

@api_bp.route('/nodes/add_nodes', methods=['POST'])
def add_nodes():
    """Adds new neighboring nodes to the network."""
    values = request.get_json()
    nodes = values.get('nodes')
    
    if nodes is None:
        return jsonify({'error': "Error, missing 'nodes' list"}), 400

    for node in nodes:
        blockchain.add_node(node)
    
    response = {
        'message': "New node(s) have been added",
        'total_nodes': list(blockchain.nodes)
    }
    return jsonify(response), 200

@api_bp.route('/nodes/sync', methods=['GET'])
def sync():
    """Performs consensus: replaces the chain if a longer, valid chain is found."""
    updated = blockchain.update_blockchain()
    
    if updated:
        response = {
            'message': 'Blockchain has been updated with the latest data (Longest chain found)',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Blockchain is already using the latest data (No longer chain found)',
            'current_chain': blockchain.chain
        }
    return jsonify(response), 200