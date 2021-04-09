from hashlib import sha256
from time import time


class Blobchain:
    def __init__(self):
        self.chain = []
        self.genesis_block()

    def genesis_block(self):
        # Initialises the blockchain with the genesis block
        self.chain.append(Blob(0, "1", None, None, None))
        pass

    def new_block(self, recipient, sender, amount):
        """Creates a new Block
        :param recipient: <str> Address of the Recipient
        :param sender: <str> Address of the Sender
        :param amount: <int> Amount of money transferred"""
        index = len(self.chain) + 1
        previous_hash = self.chain[-1].own_hash
        self.add_block(Blob(index, previous_hash, recipient, sender, amount))

    def add_block(self, block):
        """Adds a new Block to the Blockchain given the Proof of Work"""
        if self.proof_of_work(block):
            self.chain.append(block)

    def proof_of_work(self, block):
        """Verifies whether the Nonce generates a hash with 3 leading zeroes
        :param block: <class> Block
        :return: <bool>"""
        guess_hash = sha256(f"{block.index - 1}{block.nonce}{block.previous_hash}".encode()).hexdigest()
        return guess_hash[:3] == "000"


class Blob:
    def __init__(self, index, previous_hash, recipient, sender, amount, nonce=0):
        """Initialises a Block
        :param index: <int> Index of a Block in the Blockchain
        :param previous_hash: <str> SHA256 hash of the preceding Block in the Blockchain
        :param nonce: <int> Guess number for Proof of Work
        """
        self.index = index
        self.timestamp = time()
        self.previous_hash = previous_hash
        self.nonce = self.work(nonce)
        self.own_hash = self.create_hash()
        self.transaction = self.transaction(recipient, sender, amount)

    def create_hash(self):
        """Generates a SHA256 hash for the new Block
        :return: <str>"""
        data = f"{self.index}{self.timestamp}{self.previous_hash}{self.transaction}"
        new_hash = sha256(data.encode()).hexdigest()
        return new_hash

    def work(self, nonce):
        """Solves for Nonce
        :return: <int> nonce"""
        while sha256(f"{self.index - 1}{nonce}{self.previous_hash}".encode()).hexdigest()[:3] != "000":
            nonce += 1
        return nonce

    def transaction(self, recipient, sender, amount):
        """Adds the new transaction to the Block waiting to be mined"""
        transaction = {
            "recipient": recipient,
            "sender": sender,
            "amount": amount
        }
        return transaction
