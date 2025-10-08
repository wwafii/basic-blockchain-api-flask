# core/blockchain.py

import hashlib
import json
from time import time
from urllib.parse import urlparse

import requests

class Blockchain(object):
    """
    The class responsible for managing the blockchain (chain), 
    transactions, and consensus mechanism (Proof-of-Work, chain validation).
    """
    difficulty_target = "0000"

    def __init__(self):
        self.nodes = set()
        self.chain = []
        self.current_transactions = []
        
        # Create the genesis block (the first block)
        genesis_hash = self.hash_block("genesis_block")
        self.append_block(
            hash_of_previous_block = genesis_hash,
            nonce = self.proof_of_work(0, genesis_hash, [])
        )
    
    @property
    def last_block(self):
        """Returns the last block in the chain."""
        return self.chain[-1]
    
    def hash_block(self, block):
        """Creates the SHA-256 hash of a block."""
        # Ensure the dictionary is sorted for consistent hashing
        block_encoded = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_encoded).hexdigest()
    
    def proof_of_work(self, index, hash_of_previous_block, transactions):
        """
        Simple Proof of Work (PoW) algorithm: finds a nonce 
        that results in a hash starting with the 'difficulty_target'.
        """
        nonce = 0
        while self.valid_proof(index, hash_of_previous_block, transactions, nonce) is False:
            nonce += 1
        return nonce
    
    def valid_proof(self, index, hash_of_previous_block, transactions, nonce):
        """Validates if the generated hash meets the difficulty requirement (difficulty_target)."""
        # Combine all block data for hashing
        content = f'{index}{hash_of_previous_block}{transactions}{nonce}'.encode()
        content_hash = hashlib.sha256(content).hexdigest()
        
        return content_hash[:len(self.difficulty_target)] == self.difficulty_target
    
    def append_block(self, nonce, hash_of_previous_block):
        """Adds a new block to the chain."""
        block = {
            'index': len(self.chain),
            'timestamp': time(),
            'transaction': self.current_transactions,
            'nonce': nonce,
            'hash_of_previous_block': hash_of_previous_block
        }
        
        # Reset the transaction list for the next block
        self.current_transactions = []
        self.chain.append(block)
        return block
    
    def add_transaction(self, sender, recipient, amount):
        """Adds a new transaction to the current list of transactions."""
        self.current_transactions.append({
            'amount': amount,
            'recipient': recipient,
            'sender': sender,
        })
        # Returns the index of the block the transaction will be added to
        return self.last_block['index'] + 1
    
    # --- Network Mechanisms (Nodes and Consensus) ---
    
    def add_node(self, address):
        """Adds a new node (peer) to the list of nodes."""
        parse_url = urlparse(address)
        if parse_url.netloc:
            self.nodes.add(parse_url.netloc)
        print(f"Node added: {parse_url.netloc}")

    def valid_chain(self, chain):
        """Validates the integrity of the chain: each block has a valid hash and correct PoW."""
        last_block = chain[0]
        current_index = 1
        
        while current_index < len(chain):
            block = chain[current_index]
            
            # 1. Check if the hash of the previous block is correct
            if block['hash_of_previous_block'] != self.hash_block(last_block):
                return False
            
            # 2. Check if the Proof of Work (nonce) is valid
            if not self.valid_proof(
                block['index'],
                block['hash_of_previous_block'],
                block['transaction'],
                block['nonce']):
                return False
            
            last_block = block
            current_index += 1
        
        return True
    
    def update_blockchain(self):
        """Consensus Mechanism: Replaces our chain with the longest valid chain from neighboring nodes."""
        neighbours = self.nodes
        new_chain = None
        max_length = len(self.chain)
        
        for node in neighbours:
            try:
                # Retrieve the full chain from the other node
                response = requests.get(f"http://{node}/blockchain", timeout=5) 
            except requests.exceptions.RequestException as e:
                print(f"Connection failed to node {node}: {e}")
                continue
            
            if response.status_code == 200:
                data = response.json()
                length = data.get('length')
                chain = data.get('chain')
                
                # Check if the chain is longer and valid
                if length is not None and chain is not None and length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain
                
        if new_chain:
            self.chain = new_chain
            return True
        
        return False