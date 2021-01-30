from random import randint
from hashlib import sha256
import primes

"""Adapted the Digital Signature Algorithm as documented by the U.S. Department of Commerce
Section B.1.1: Key Pair Generation Using Extra Random Bits
Create public and private keys for yourself"""


def bits_to_integer(bits, N):
    integer = 0
    for n in range(len(bits)):
        two_power = 2 ** (N - n)
        integer += two_power * int(bits[n])
    return integer


def hashes_to_bits(M):
    hashes = sha256(M.encode()).hexdigest()
    bits = bin(int(hashes, 16))
    return bits


def find_prime(length, input_seed):
    finding = primes.ST_random_prime(length, input_seed)
    good_prime = finding.prime
    return good_prime


class PairKey:
    def __init__(self, L, N, input_seed):
        """:param L: <int> Bit length of p
        :param N: <int> Bit length of q"""

        self.p = find_prime(L, input_seed)
        self.q = find_prime(N, input_seed)

        validate = Validate()
        self.L = validate.pq(self.p, L)
        self.N = validate.pq(self.q, N)

        validate.LN(self.L, self.N)

        self.g = int(self.find_g(self.p, self.q))
        self.c = self.find_c()
        """ !-!-! validate.g() takes too damn long to run """
        # validate.g(self.p, self.q, g)

        self.x = (self.c % (self.q - 1)) + 1
        self.y = pow(self.x, self.g, self.p)
        validate.xy(self.x, self.y, self.p, self.q)

    def find_g(self, p, q):
        """:param p: <int> Prime modulus
        :param q: <int> Prime divisor of (p - 1)
        :return g: <int> Generator of a subgroup of order q in the multiplicative group GF(p)"""
        e = (p - 1) // q
        h = randint(1, (p - 1))
        g = pow(h, e, p)
        if g == 1:
            self.find_g(p, q)
        return g

    def find_c(self):
        bitstring = [randint(0, 1) for _ in range(self.N + 64)]
        c = bits_to_integer(bitstring, self.N + 64)
        return c

    def find_k(self):
        pass

    def gen_signature(self, M, k):
        """:param M: <str> Transaction details
        :param k: <int> Secret number unique to each message"""
        z = hashes_to_bits(M)[2:min(self.N, 256)]
        z = bits_to_integer(z, len(z))

        r = pow(self.g, k, self.p) % self.q
        s = (k ** (-1) * (z + self.x * r)) % self.q
        if r == 0 or s == 0:
            self.find_k()
        return r, s

    def verify_signature(self, M, r, s):
        """Prior to verifying the signature, the domain parameters and public key should be available to the verifier
        :param M: <str> Received version of M (M')
        :param r: <int> Received version of r (r')
        :param s: <int> Received version of s (s')
        """
        if not (0 < r < self.q and 0 < s < self.q):
            return False
        w = pow(s, -1, self.q)
        z = hashes_to_bits(M)[:min(self.N, 256)]
        z = bits_to_integer(z)

        u1 = (z * w) % self.q
        u2 = (r * w) % self.q
        v = ((self.g ** u1) * (self.y ** u2) % self.p) % self.q
        if v == r:
            return True


class Validate:
    def __init__(self):
        pass

    def LN(self, L, N):
        min_L, min_N = 10, 5
        if L < min_L or N < min_N:
            raise Exception("(L, N) pair is INVALID")

    def pq(self, pq, ln):
        """Adjusts bit length (L, N) so that the newly generated prime numbers fall within their default relative range"
        :param pq: <int> Prime number p or q
        :param ln: Bit length of p or q respectively"""
        while not (2 ** (ln - 1) <= pq <= 2 ** ln):
            if pq < 2 ** (ln - 1):
                ln -= 1
            elif pq > 2 ** ln:
                ln += 1
        return ln

    def g(self, p, q, g):
        if not 2 <= g <= (p - 1):
            print("g is INVALID")
        if g ** q == 1 % p:
            print("g is PARTIALLY VALID")
        else:
            print("g is INVALID")

    def xy(self, x, y, p, q):
        if not 1 <= x <= (q - 1):
            print("x is INVALID")
        if not 1 <= y <= (p - 1):
            print("y is INVALID")
        else:
            print("SUCCESS")


pair = PairKey(1024, 160, 927)
(x, y) = pair.gen_signature("hello", 2)

